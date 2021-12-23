# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Userinfo(AbstractUser):
    # 用户id
    uid = models.BigAutoField(primary_key=True)
    # 用户邮箱
    email = models.EmailField(unique=True)

