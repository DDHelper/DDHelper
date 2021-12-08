import warnings

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
        query = Dynamic.objects.filter(member__in=list(group.members.all().values_list('mid', flat=True)))
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


class SyncTask(models.Model):
    uuid = models.UUIDField(primary_key=True)
    fail_msg = models.TextField(null=True)

    def __str__(self):
        return str(self.uuid)


class DynamicSyncInfo(models.Model):
    sid = models.BigAutoField(primary_key=True)
    sync_start_time = models.DateTimeField(auto_now_add=True)
    sync_update_time = models.DateTimeField(auto_now=True)

    total_tasks = models.ManyToManyField(SyncTask, related_name="info_total_tasks")
    success_tasks = models.ManyToManyField(SyncTask, related_name="info_success_tasks")
    failed_tasks = models.ManyToManyField(SyncTask, related_name="info_failed_tasks")

    def finish(self):
        return self.pending_tasks == 0

    @property
    def pending_tasks(self):
        pending = self.total_tasks.count() - self.success_tasks.count() - self.failed_tasks.count()
        if pending < 0:
            warnings.warn(f"sid={self.sid} Pending < 0")
            return 0
        return pending

    @property
    def time_cost(self):
        return self.sync_update_time - self.sync_start_time

    @classmethod
    def get_latest(cls):
        return DynamicSyncInfo.objects.order_by('-sid').first()

    def as_dict(self):
        return {
            'sid': self.sid,
            'finish': self.finish(),
            'time_cost': self.time_cost,
            'sync_start_time': self.sync_start_time,
            'sync_update_time': self.sync_update_time,
            'total_tasks': self.total_tasks.count(),
            'pending_tasks': self.pending_tasks,
            'success_tasks': self.success_tasks.count(),
            'failed_tasks': self.failed_tasks.count(),
        }

    def __str__(self):
        return str(self.as_dict())

