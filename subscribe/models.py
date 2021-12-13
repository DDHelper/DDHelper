from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q

from account.models import Userinfo


DEFAULT_GROUP_NAME = "默认分组"


# Create your models here.
class SubscribeMember(models.Model):
    # b站mid
    mid = models.BigIntegerField(primary_key=True)
    # b站用户名
    name = models.CharField(max_length=50)
    # 头像url
    face = models.URLField(max_length=200)
    # 最近用户数据更新时间（头像、昵称)
    last_profile_update = models.DateTimeField(auto_now=True)

    def as_dict(self):
        """
        暂时替代序列化的一种实现
        :return:
        """
        # TODO 使用序列化器
        return {
            'mid': self.mid,
            'name': self.name,
            'face': self.face,
        }


class MemberGroup(models.Model):
    # 用户分组编号
    gid = models.BigAutoField(primary_key=True)
    # 用户id
    user = models.ForeignKey(Userinfo, on_delete=models.CASCADE)
    # 用户分组名
    group_name = models.CharField(max_length=100)
    # 具体分组成员
    members = models.ManyToManyField(SubscribeMember)

    @classmethod
    def get_or_create_default_group(cls, aid):
        """
        获取或者创建用户的默认分组
        :param aid:
        :return: (Userinfo, bool)
        """
        return MemberGroup.objects.get_or_create(user_id=aid, group_name=DEFAULT_GROUP_NAME)

    @classmethod
    def get_group(cls, aid, gid):
        if gid == 0:
            return MemberGroup.get_or_create_default_group(aid=aid)[0]
        else:
            return MemberGroup.objects.filter(Q(user=aid) & Q(gid=gid)).first()

    @classmethod
    def select_groups_by_account(cls, aid):
        """
        根据一个账号查找所有分组
        :param aid:
        :return:
        """
        query = MemberGroup.objects.filter(user=aid)
        if not query.exists():
            MemberGroup.get_or_create_default_group(aid)
        return query

    @classmethod
    def select_groups_by_account_and_member(cls, aid, mid):
        """
        查找一个用户关注的某个成员所在的分组列表
        :param mid:
        :return:
        """
        return SubscribeMember.objects.get(mid=mid).membergroup_set.filter(user=aid)

    @classmethod
    def is_subscribed(cls, aid, mid):
        """
        查询一个用户是否关注了某个成员
        :param aid:
        :param mid:
        :return:
        """
        try:
            member = SubscribeMember.objects.get(mid=mid)
            return member.membergroup_set.filter(user=aid).exists()
        except SubscribeMember.DoesNotExist:
            return False

    @classmethod
    def set_groups_by_account_and_member(cls, aid, mid, groups):
        """
        修改一个用户关注的某个成员所在的分组列表
        :param aid:
        :param mid:
        :param groups:
        :return:
        """
        member = SubscribeMember.objects.get(mid=mid)
        old_groups = set(MemberGroup.select_groups_by_account_and_member(aid, mid).values_list('gid', flat=True))
        new_groups = set(groups)
        to_delete = old_groups - new_groups
        to_add = new_groups - old_groups
        if len(to_delete) > 0:
            # 从旧分组中移除
            member.membergroup_set.remove(*to_delete)
        if len(to_add) > 0:
            # 检测新加的分组是不是属于这个用户
            if MemberGroup.objects.filter(gid__in=to_add).exclude(user=aid).exists():
                # 新加的分组里有不属于这个用户的
                raise PermissionDenied("无权访问部分分组")
            # 添加进新分组
            member.membergroup_set.add(*to_add)
