from django.db import models
from dynamic.models import Dynamic
# Create your models here.


class TimelineDynamicProcessInfo(models.Model):
    PENDING = 0
    VERSION = 1

    dynamic = models.OneToOneField(
        Dynamic,
        on_delete=models.CASCADE,
        primary_key=True)

    process_version = models.IntegerField(default=0)

    @classmethod
    def get(cls, dynamic_id):
        """

        :rtype: TimelineDynamicProcessInfo
        """
        return TimelineDynamicProcessInfo.objects.get_or_create(dynamic_id=dynamic_id)[0]

    def should_update(self):
        """
        如果数据库中记录的version小于当前的version，表示动态处理系统更新，需要重新处理
        :return:
        """
        return self.process_version < TimelineDynamicProcessInfo.VERSION

    def apply_update(self):
        """
        当动态处理完后更新版本
        :return:
        """
        self.process_version = TimelineDynamicProcessInfo.VERSION
        self.save()


class TimelineEntry(models.Model):
    # 动态摘要信息
    text = models.JSONField()
    # 对应的原动态
    dynamic = models.OneToOneField(
        Dynamic,
        on_delete=models.CASCADE,
        primary_key=True)
    # 提取的动态含有的时间信息
    event_time = models.DateTimeField()
    # 动态类型类别
    EVENT_TYPE = [
        ('UN', 'Unknown'),
        ('ST', 'Stream'),
        ('LO', 'Lottery'),
        ('RE', 'Release')
    ]
    type = models.CharField(
        max_length=2,
        choices=EVENT_TYPE,
        default='NT'
    )
