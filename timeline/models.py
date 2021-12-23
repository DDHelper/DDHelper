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
        按id获取某个timeline处理过程
        :param dynamic_id: 需要获取的处理过程id
        :return: TimelineDynamicProcessInfo 获取到的分组
        """
        return TimelineDynamicProcessInfo.objects.get_or_create(dynamic_id=dynamic_id)[0]

    def should_update(self):
        """
        返回当前动态是否需要更新
        :return: Bool 需要更新返回True，否则返回False
        """
        return self.process_version < TimelineDynamicProcessInfo.VERSION

    def apply_update(self):
        """
        动态更新完后更新版本号
        :return: None
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
    # 动态类型类别，依次是位置类别、直播类别、抽奖类别、视频投稿类别
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

    # 声明类在数据库中的排序方式和索引便于加速查找
    class Meta:
        ordering = ['-event_time']
        indexes = [models.Index(fields=['event_time'])]

    @classmethod
    def select_entry_in_group(cls, group, offset):
        """
        选择一个分组中的timeline对象，从时间小于time_end算起
        :param group: 要选择的timeline对象所在的分组
        :param offset: 时间上的最大值
        :return: QuerySet 包含所有满足条件的timeline
        """
        query = TimelineEntry.objects.filter(dynamic__member__in=list(group.members.all().values_list('mid', flat=True)))
        if offset is not None:
            query = query.filter(event_time__lt=offset)
        return query.order_by('-event_time')

    def as_dict(self):
        """
        返回timeline对象作为文本输出的信息
        :return: dict timeline的基本信息
        """
        return {
            'dynamic_id': self.dynamic_id,
            'text': self.text,
            'event_time': self.event_time.timestamp(),
            'type': self.type,
            'raw': self.dynamic.raw
        }

    def __str__(self):
        """
        返回timeline对象作为文本输出的信息
        :return: string timeline的基本信息以字典文本串形式输出
        """
        return str(self.as_dict())
