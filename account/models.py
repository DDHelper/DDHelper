from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser


class Userinfo(AbstractUser):
    uid = models.BigAutoField(primary_key=True)

    def __str__(self):
        return str(self.uid)
