from django.db import models
import uuid


class PostContent(models.Model):
    """post content model"""
    post_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
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
    review_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Post {self.post.post_id} Statistics"

class Review(models.Model):
    """Post review model - storing user reviews for posts"""
    post = models.ForeignKey(PostContent, on_delete=models.CASCADE, related_name='reviews', db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews', db_index=True)
    comment = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Review by User {self.user.user_id} for Post {self.post.post_id}"

class Reply(models.Model):
    """Post reply model - storing user replies to reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies', db_index=True)
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, related_name='child_replies', null=True, blank=True, db_index=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='replies', db_index=True)
    comment = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)

    def __str__(self):
        if self.parent_reply_id:
            return f"Reply by User {self.user.user_id} for Reply {self.parent_reply_id}"
        return f"Reply by User {self.user.user_id} for Review {self.review_id}"

class Favorite(models.Model):
    """Post favorite model - storing user favorites for posts"""
    post = models.ForeignKey(PostContent, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='favorite_records')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 同一用户不能重复收藏同一帖子

    def __str__(self):
        return f"User {self.user.user_id} favorited Post {self.post.post_id}"