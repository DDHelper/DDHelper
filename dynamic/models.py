from django.db import models

from subscribe.models import SubscribeMember


class DynamicMember(models.Model):
    # b站mid
    mid = models.OneToOneField(SubscribeMember, on_delete=models.CASCADE, primary_key=True)
    # 最近更新动态页面的时间
    last_dynamic_update = models.DateTimeField(auto_now=True)


class Dynamic(models.Model):
    # 动态id
    dynamic_id = models.BigIntegerField(primary_key=True)
    # 发动态的b站用户
    member = models.ForeignKey(SubscribeMember, on_delete=models.CASCADE)
    # 动态的种类，参考：https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/dynamic/get_dynamic_detail.md
    dynamic_type = models.IntegerField()
    # 动态的时间戳
    timestamp = models.DateTimeField()
    # 原始动态数据
    raw = models.JSONField()

    @classmethod
    def select_dynamics_in_group(cls, group, offset):
        query = Dynamic.objects.filter(member__in=group.members.all())
        if offset != 0:
            query = query.filter(dynamic_id__lte=offset)
        return query.order_by('-dynamic_id')

    def as_dict(self):
        return {
            "dynamic_id": self.dynamic_id,
            "mid": self.member_id,
            "dynamic_type": self.dynamic_type,
            "timestamp": self.timestamp.timestamp(),
            "raw": self.raw
        }

