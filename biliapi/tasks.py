import logging
import time
from contextlib import contextmanager
from functools import wraps

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from DDHelper import settings

logger: logging.Logger = get_task_logger(__name__)


# 默认每次请求后的等待时间（秒）
# 推荐每台机器最多两个worker
DEFAULT_WAIT = 1.5 if not settings.TESTING else 0.1
DEFAULT_TIMEOUT = 10

BLOCKED = False
BLOCKED_START_TIME = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4146.4 Safari/537.36'
}


class BlockedException(Exception):
    def __init__(self, msg):
        super(BlockedException, self).__init__(msg)


def get_random_proxy():
    """
    get random proxy from proxypool
    :return: proxy
    """
    if settings.PROXY_POOL:
        return {'http': "http://" + requests.get(settings.PROXY_POOL).text.strip()}
    else:
        return None


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
        global BLOCKED, BLOCKED_START_TIME
        if not BLOCKED:
            set_blocked()


def set_blocked():
    """
    将当前状态设置为BLOCKED
    :return:
    """
    global BLOCKED, BLOCKED_START_TIME
    BLOCKED = True
    from django.utils import timezone
    import pytz
    BLOCKED_START_TIME = timezone.now().astimezone(pytz.timezone("Asia/Shanghai"))
    print(f"[{BLOCKED_START_TIME}] 当前机器或ip可能被b站拦截，已停止所有请求，请管理员手动处理")
    import celery.worker.control as control
    control.disable_events()
    print(f"已停止任务队列")


def check_security():
    """
    在尝试发出请求前做安全检测，默认延迟一段时间，并在被拦截时停止发送新的请求
    :return:
    """
    if BLOCKED:
        raise BlockedException(f"[{BLOCKED_START_TIME}] 当前机器或ip可能被b站拦截，已停止所有请求，请管理员手动处理")


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
@with_default_wait
def space_history(host_uid: int, offset_dynamic_id: int):
    """
    获取动态列表
    :param host_uid: 用户id
    :param offset_dynamic_id: 起始动态id，默认为0（获取最新的动态），不包括这个id的动态
    :return:
    """
    check_security()
    rsp = requests.get(
        "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history",
        params={
            "visitor_uid": 0,
            "host_uid": host_uid,
            "offset_dynamic_id": offset_dynamic_id
        },
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
        proxies=get_random_proxy()
    )
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


# noinspection PyTypeChecker
@shared_task()
@with_default_wait
def user_profile(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    check_security()
    rsp = requests.get(
        "https://api.bilibili.com/x/space/acc/info",
        params={
            "mid": mid,
            "jsonp": "jsonp"
        },
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
        proxies=get_random_proxy()
    )
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


# noinspection PyTypeChecker
@shared_task()
def user_stat(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    check_security()
    rsp = requests.get(
        "https://api.bilibili.com/x/relation/stat",
        params={
            "vmid": mid,
            "jsonp": "jsonp"
        },
        headers=headers,
        timeout=DEFAULT_TIMEOUT)
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


# noinspection PyTypeChecker
@shared_task
def search_user_name(name: str):
    """
    根据关键字搜索用户名
    由于对于延迟敏感，不使用代理池，也不使用默认延迟
    :param name: 关键字
    :return:
    """
    check_security()
    rsp = requests.get("http://api.bilibili.com/x/web-interface/search/type",
                       params={
                           "search_type": "bili_user",
                           "keyword": name
                       },
                       timeout=DEFAULT_TIMEOUT)
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


# noinspection PyTypeChecker
@shared_task
def search_user_id(mid: int):
    """
    获取mid对应的成员的信息
    由于对于延迟敏感，不使用代理池，也不使用默认延迟
    :param mid:
    :return:
    """
    check_security()
    rsp = requests.get("http://api.bilibili.com/x/web-interface/search/all/v2",
                       params={
                           "search_type": "bili_user",
                           "keyword": f'uid:{mid}'
                       },
                       timeout=DEFAULT_TIMEOUT)
    check_response(rsp)
    if rsp.status_code != 200:
        return None
    else:
        return rsp.json()


if __name__ == '__main__':
    # print(space_history(557839, 5190712790698414))
    print(user_profile(489391680))

