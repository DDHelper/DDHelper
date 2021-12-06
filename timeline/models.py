from django.db import models
from dynamic.models import Dynamic
# Create your models here.


class TimelineEntry(models.Model):
    # 动态摘要信息
    text = models.JSONField()
    # 对应的原动态
    dynamic = models.OneToOneField(
        Dynamic,
        on_delete=models.CASCADE,
        primary_key=False)
    # 提取的动态含有的时间信息
    event_time = models.DateTimeField()
    # 动态类型类别
    EVENT_TYPE = [
        ('NT', 'Non-time'),
        ('ST', 'Stream'),
        ('LO', 'Lottery'),
        ('RE', 'Release')
    ]
    type = models.CharField(
        max_length=2,
        choices=EVENT_TYPE,
        default='NT'
    )
