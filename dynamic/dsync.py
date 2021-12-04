from biliapi.tasks import get_data_if_valid, user_profile, space_history
from .models import DynamicMember, Dynamic
from subscribe.models import SubscribeMember
from django.utils import timezone
import warnings
import pytz

CST_TIME_ZONE = pytz.timezone("Asia/Shanghai")


class DsyncException(Exception):
    def __init__(self, msg):
        super(DsyncException, self).__init__(msg)


def get_subscribe_member(mid: int):
    """
    获取一个成员，如果没有添加过则返回None
    :param mid: 成员id
    :rtype: SubscribeMember
    :return: 获取到的成员
    """
    try:
        return SubscribeMember.objects.get(mid=mid)
    except SubscribeMember.DoesNotExist:
        return None


def get_dynamic_member(mid: int):
    """
        获取一个成员，如果没有添加过则返回None
        :param mid: 成员id
        :rtype: SubscribeMember
        :return: 获取到的成员
        """
    try:
        return DynamicMember.objects.get(mid_id=mid)
    except DynamicMember.DoesNotExist:
        return None


def update_member_profile(member: SubscribeMember, data=None, auto_save=True):
    """
    更新成员的相关信息（不会提交到数据库）
    :param member: 需要更新的成员
    :param data: 用于更新的数据，如果为None则主动从bilibili拉取相关信息来填充
    :param auto_save: 是否自动保存，默认为true
    :return: 如果成功则返回None，否则返回错误信息
    """
    if data is None:
        data, msg = get_data_if_valid(user_profile(member.mid))
        if data is None:
            return msg or "unknown"
    if member.mid != data['mid']:
        return "mid mismatch"
    member.name = data['name']
    member.face = data['face']
    if auto_save:
        member.save()


def get_saved_latest_dynamic(member: int):
    """
    获取这个成员在数据库中同步过的最新的一条动态
    :rtype: Dynamic
    :return: 获取失败时返回None
    """
    try:
        return Dynamic.objects.filter(member__mid=member).order_by("-dynamic_id")[0]
    except IndexError:
        return None


def get_all_dynamic_since(member: SubscribeMember, dynamic_id, max_count=50, max_time=30):
    """
    获取这个dynamic_id前的所有动态，按dynamic_id增续排列
    :param member:
    :param dynamic_id:
    :param max_count: 最大动态条数，只用来判断中止，返回数据可能超过这个量
    :param max_time: 最长同步时间
    :return: 获取到的动态，发生错误时的错误信息
    """
    dynamics = []
    next_offset = 0
    while True:
        rsp = space_history(member.mid, next_offset)
        data, msg = get_data_if_valid(rsp)
        if data is None:
            return None, msg
        if data['has_more'] == 0:
            break
        cards = data['cards']
        cards.sort(key=lambda c: c["desc"]["dynamic_id"], reverse=True)  # 降序排列
        break_outer = False
        for card in cards:
            dy = parse_dynamic_card(card, member=member)
            if dy.dynamic_id <= dynamic_id:
                break_outer = True
                break  # 已经到达了目标位置
            else:
                dynamics.append(dy)
        if data['has_more'] == 1:
            next_offset = data['next_offset']
        if len(dynamics) >= max_count or break_outer:
            break
        # TODO：根据时间判断是否终止循环
    return dynamics, None


def parse_dynamic_card(card, member: SubscribeMember = None, set_member=False):
    """
    将一个card解析为一个Dynamic对象
    :param card: 原始json数据
    :param member: 预设的member变量
    :param set_member: 是否自动设置Dynamic.member
    :rtype: Dynamic
    :return:
    """
    desc = card['desc']
    dy = Dynamic()
    dy.dynamic_id = desc['dynamic_id']
    dy.dynamic_type = desc['type']
    dy.timestamp = timezone.datetime.fromtimestamp(desc['timestamp'], tz=CST_TIME_ZONE)
    dy.raw = card

    if member is not None:
        if member.mid != desc['uid']:
            warnings.warn("预设的member与card中的数据不匹配")
            return None
        else:
            dy.member = member
    if set_member:
        if dy.member is None:
            dy.member = get_subscribe_member(desc['uid'])
        if dy.member is None:
            return None
    return dy
