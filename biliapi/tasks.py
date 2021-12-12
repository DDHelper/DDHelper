import logging
import time
from contextlib import contextmanager
from functools import wraps

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from requests.exceptions import ConnectTimeout, ReadTimeout, ProxyError

from DDHelper import settings

logger: logging.Logger = get_task_logger(__name__)


# 默认每次请求后的等待时间（秒）
# 推荐每台机器最多两个worker
DEFAULT_WAIT = 1.5 if not settings.TESTING else 0.1
DEFAULT_TIMEOUT = 10

BLOCKED = False
BLOCKED_START_TIME = None

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4146.4 Safari/537.36'
}


GOOD_PROXY = None
GOOD_PROXY_CALLS = 0


def get_random_proxy(retry=0, check_proxy=True):
    """
    get random proxy from proxypool
    :return: proxy
    """
    global GOOD_PROXY, GOOD_PROXY_CALLS
    if GOOD_PROXY is not None:
        if GOOD_PROXY_CALLS < 20:
            return GOOD_PROXY
        else:
            logger.info(f"超过最大调用次数, 重置 {GOOD_PROXY}")
            GOOD_PROXY = None
            GOOD_PROXY_CALLS = 0

    if retry > 5:
        return None
    if settings.PROXY_POOL:
        proxies = {'http': "http://" + requests.get(settings.PROXY_POOL).text.strip()}
        if check_proxy:
            rsp = client_info(proxies)
            if rsp:
                logger.info(f"使用代理: {proxies}")
                GOOD_PROXY = proxies
                GOOD_PROXY_CALLS = 0
                return proxies
            else:
                return get_random_proxy(retry=retry + 1, check_proxy=check_proxy)
        else:
            return proxies
    else:
        return None


def client_info(proxies=None):
    try:
        if proxies is None:
            proxies = get_random_proxy(check_proxy=False)
        rsp = requests.get(
            "http://api.bilibili.com/client_info",
            headers=USER_AGENT,
            timeout=3,
            proxies=proxies
        )
        if rsp.status_code != 200:
            return None
        else:
            return rsp.json()
    except Exception:
        return None


@contextmanager
def _clear_proxy_info():
    try:
        yield
    except Exception as e:
        global GOOD_PROXY, GOOD_PROXY_CALLS
        GOOD_PROXY = None
        GOOD_PROXY_CALLS = 0
        logger.info(f"发生错误, 重置 {GOOD_PROXY} e: {e}")
        raise e


def clear_proxy_info_on_error(func):
    @wraps(func)
    def call_func(*args, **kwargs):
        with _clear_proxy_info():
            return func(*args, **kwargs)

    return call_func


@contextmanager
def _default_wait():
    """
    每次请求后的等待时间，防止请求被拦截
    """
    start_time = time.time()
    try:
        yield
    except Exception as e:
        raise e
    else:
        time_cost = time.time() - start_time
        if time_cost < DEFAULT_WAIT:
            time.sleep(DEFAULT_WAIT - time_cost)


def with_default_wait(func):
    """
    控制一个请求的耗时
    """
    @wraps(func)
    def call_func(*args, **kwargs):
        with _default_wait():
            return func(*args, **kwargs)
    return call_func


def check_response(rsp):
    """
    检查一个请求是否被拦截，拦截后将系统设置为BLOCKED模式，停止发送请求
    :param rsp:
    :return:
    """
    if rsp.status_code == 412:
        set_blocked()


def set_blocked():
    """
    将当前状态设置为BLOCKED
    :return:
    """
    global BLOCKED, BLOCKED_START_TIME
    BLOCKED = True

    global GOOD_PROXY, GOOD_PROXY_CALLS
    GOOD_PROXY = None
    GOOD_PROXY_CALLS = 0
    logger.info(f"代理被拦截, 重置 {GOOD_PROXY}")

    from django.utils import timezone
    import pytz
    BLOCKED_START_TIME = timezone.now().astimezone(pytz.timezone("Asia/Shanghai"))
    logger.info(f"[{BLOCKED_START_TIME}] 当前机器或ip可能被b站拦截，已停止所有请求，请管理员手动处理")


def api_retry(func):
    """
    允许三次重试
    :param func:
    :return:
    """
    @wraps(func)
    def call_func(*args, **kwargs):
        retry = 0
        while retry < 4:
            try:
                result = func(*args, **kwargs)
                if result is None:
                    retry += 1
                else:
                    return result
            except Exception:
                retry += 1
    return call_func


# noinspection PyTypeChecker
def call_api(url, params=None, headers=None, timeout=DEFAULT_TIMEOUT, **kwargs):
    if headers is None:
        headers = USER_AGENT
    # 使用代理的情况下不进行拦截判定
    # check_security()
    rsp = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
        proxies=kwargs['proxies'] if 'proxies' in kwargs else get_random_proxy()
    )
    check_response(rsp)
    if rsp.status_code != 200:
        try:
            body = rsp.json()
            logger.warning(f"Bad Api Call[{rsp.status_code}]: {body}")
        except Exception:
            logger.warning(f"Bad Api Call[{rsp.status_code}]: None")
        return None
    else:
        return rsp.json()


def get_data_if_valid(rsp, fallback_msg="unknown"):
    """
    如果rsp合理，则提取出data部分，否则返回None
    :param rsp: 需要做提取的json
    :param fallback_msg: rsp为None时的错误信息
    :return: json里的data部分, 发生错误时的错误信息
    """
    if rsp is None:
        return None, fallback_msg
    if rsp['code'] == 0:
        return rsp['data'], None
    else:
        return None, rsp['msg']


# noinspection PyTypeChecker
@shared_task()
@api_retry
@clear_proxy_info_on_error
@with_default_wait
def space_history(host_uid: int, offset_dynamic_id: int):
    """
    获取动态列表
    :param host_uid: 用户id
    :param offset_dynamic_id: 起始动态id，默认为0（获取最新的动态），不包括这个id的动态
    :return:
    """
    return call_api(
        "http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history",
        params={
            "visitor_uid": 0,
            "host_uid": host_uid,
            "offset_dynamic_id": offset_dynamic_id
        },
    )


# noinspection PyTypeChecker
@shared_task()
@api_retry
@clear_proxy_info_on_error
@with_default_wait
def user_profile(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    return call_api(
        "http://api.bilibili.com/x/space/acc/info",
        params={
            "mid": mid,
            "jsonp": "jsonp"
        },
    )


# TODO 部分要求低延迟的api需要一个不使用代理的解决方案

# noinspection PyTypeChecker
@shared_task()
@clear_proxy_info_on_error
def user_stat(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    return call_api(
        "http://api.bilibili.com/x/relation/stat",
        params={
            "vmid": mid,
            "jsonp": "jsonp"
        },
        proxies=None
    )


# noinspection PyTypeChecker
@shared_task
@clear_proxy_info_on_error
def search_user_name(name: str):
    """
    根据关键字搜索用户名
    由于对于延迟敏感，不使用代理池，也不使用默认延迟
    :param name: 关键字
    :return:
    """
    return call_api(
        "http://api.bilibili.com/x/web-interface/search/type",
        params={
            "search_type": "bili_user",
            "keyword": name
        },
        proxies=None
    )


# noinspection PyTypeChecker
@shared_task
def search_user_id(mid: int):
    """
    获取mid对应的成员的信息
    由于对于延迟敏感，不使用代理池，也不使用默认延迟
    :param mid:
    :return:
    """
    return call_api(
        "http://api.bilibili.com/x/web-interface/search/all/v2",
        params={
            "search_type": "bili_user",
            "keyword": f'uid:{mid}'
        },
        proxies=None
    )


if __name__ == '__main__':
    # print(client_info())
    print(space_history(557839, 0))
    # print(user_profile(489391680))

