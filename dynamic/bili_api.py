import requests


# noinspection PyTypeChecker
def space_history(host_uid: int, offset_dynamic_id: int):
    """
    获取动态列表
    :param host_uid: 用户id
    :param offset_dynamic_id: 起始动态id，默认为0（获取最新的动态），不包括这个id的动态
    :return:
    """
    rsp = requests.get(
        "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history",
        params={
            "visitor_uid": 0,
            "host_uid": host_uid,
            "offset_dynamic_id": offset_dynamic_id,
            "platform": "web"
        },
        timeout=2)
    return rsp.json()


# noinspection PyTypeChecker
def user_profile(mid: int):
    """
    获取b站用户数据
    :param mid: b站用户id
    :return:
    """
    rsp = requests.get(
        "https://api.bilibili.com/x/space/acc/info",
        params={
            "mid": mid,
            "jsonp": "jsonp"
        },
        timeout=2)
    return rsp.json()


if __name__ == '__main__':
    print(space_history(8401607, 575349833245683072))
    print(user_profile(8401607))

