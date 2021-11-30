# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Userinfo(AbstractUser):
    uid = models.BigAutoField(primary_key=True)

    def __str__(self):
        return str(self.uid)
