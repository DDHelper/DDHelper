from django.db import models

from account.models import Userinfo


# Create your models here.
class SubscribeMember(models.Model):
    # b站mid
    mid = models.BigIntegerField(primary_key=True)
    # b站用户名
    name = models.CharField(max_length=50)
    # 头像url
    face = models.URLField(max_length=200)


class UserGroup(models.Model):
    # 用户id
    user = models.ForeignKey(Userinfo, on_delete=models.CASCADE)
    # 用户分组名
    group_name = models.CharField(max_length=100)
    # 用户分组编号
    gid = models.BigAutoField(primary_key=True)


class SubscribeList(models.Model):
    # 关注的B站up主
    mem = models.ForeignKey(SubscribeMember, on_delete=models.CASCADE)
    # 所属分组
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
