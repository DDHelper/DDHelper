from django.db import models


class Member(models.Model):
    # b站mid
    mid: models.BigAutoField(primary_key=True)
    # b站用户名
    name: models.CharField(max_length=50)
    # 头像url
    face: models.URLField(max_length=200)
    # 最近用户数据更新时间（头像、昵称)
    last_profile_update: models.DateTimeField()
    # 最近更新动态页面的时间
    last_dynamic_update: models.DateTimeField()


class Dynamic(models.Model):
    # 动态id
    dynamic_id: models.BigIntegerField(primary_key=True)
    # 发动态的b站用户
    member: models.ForeignKey(Member, on_delete=models.CASCADE)
    # 动态的种类，参考：https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/dynamic/get_dynamic_detail.md
    dynamic_type: models.IntegerField()
    # 动态的时间戳
    timestamp: models.DateTimeField()
    # 原始动态数据
    raw: models.JSONField()


