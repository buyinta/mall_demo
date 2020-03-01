from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    # 增加mobile字段
    mobile = models.CharField(max_length=11,
                              unique=True,
                              verbose_name='手机号')

    # 设置表名
    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'

    # 设置魔法方法__str__，返回对象名称
    def __str__(self):
        return self.username
