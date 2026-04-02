from django.db import models
from users.models import User


class UserPost(models.Model):
    """Storage model for user-post relationships, storing userId and postId"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_posts') #on_delete=models.CASCADE表示当用户被删除时，相关的UserPost记录也会被删除，related_name='user_posts'允许我们通过user.user_posts来访问与该用户相关的所有UserPost记录
    post_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'post_id')  # 同一用户不能重复添加同一帖子

    def __str__(self):
        return f"User{self.user.user_id}'s post'{self.post_id}"


class PostContent(models.Model):
    """post content model"""
    post_id = models.OneToOneField(UserPost, on_delete=models.CASCADE, related_name='content', primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class PostStats(models.Model):
    """Post statistics model - likes, favorites, etc."""
    post = models.OneToOneField(PostContent, on_delete=models.CASCADE, related_name='stats')
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    favorites_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Post {self.post.post_id} Statistics"

class Review(models.Model):
    """Post review model - storing user reviews for posts"""
    post = models.ForeignKey(PostContent, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Review by User {self.user.user_id} for Post {self.post.post_id}"

class Reply(models.Model):
    """Post reply model - storing user replies to reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replies')
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Reply by User {self.user.user_id} for Review {self.review.id}"

class Favorite(models.Model):
    """Post favorite model - storing user favorites for posts"""
    post = models.ForeignKey(PostContent, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 同一用户不能重复收藏同一帖子

    def __str__(self):
        return f"User {self.user.user_id} favorited Post {self.post.post_id}"