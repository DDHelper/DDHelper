from django.db import models
from account.models import Userinfo
from dynamic.models import Member


# Create your models here.
class UserGroup(models.Model):
    #用户id
    user = models.ForeignKey(Userinfo, on_delete=models.CASCADE)
    #用户分组名
    group_name = models.CharField(max_length=100)
    #用户分组编号
    gid = models.BigAutoField(primary_key=True)

class SubscribeList(models.Model):
    # 关注的B站up主
    mem = models.ForeignKey(Member, on_delete=models.CASCADE)
    # 所属分组
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)