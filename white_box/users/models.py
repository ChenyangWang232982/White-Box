from django.db import models

class User(models.Model):
    """user info """
    user_id = models.AutoField(primary_key=True) #AutoField会自动递增，primary_key=True表示这是主键
    username = models.CharField(max_length=100, unique=True) #CharField表示这是一个字符串字段，max_length=100限制最大长度为100，unique=True表示用户名必须唯一
    password = models.CharField(max_length=255) #CharField表示这是一个字符串字段，max_length=255限制最大长度为255
    email = models.EmailField(unique=True) #EmailField表示这是一个邮箱字段，unique=True表示邮箱必须唯一
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  # 用户头像
    bio = models.TextField(blank=True)  # 个人简介
    is_active = models.BooleanField(default=True)  # 账户是否活跃
    phone = models.CharField(max_length=20, blank=True)  # 电话号码
    created_at = models.DateTimeField(auto_now_add=True) #DateTimeField表示这是一个日期时间字段，auto_now_add=True表示在创建对象时自动设置为当前时间
    updated_at = models.DateTimeField(auto_now=True)
    favorites = models.ManyToManyField('posts.PostContent', related_name='favorited_by', blank=True)  # 用户收藏的帖子

    def __str__(self):
        return self.username
