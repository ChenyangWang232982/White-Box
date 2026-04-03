from rest_framework import serializers
from .models import PostContent, PostStats, Review, Favorite
from users.models import User


class PostContentSerializer(serializers.ModelSerializer):
    """Serializer for PostContent model - read only"""
    user = serializers.StringRelatedField()

    class Meta:
        model = PostContent
        fields = ['post_id', 'user', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['post_id', 'created_at', 'updated_at']


class PostContentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PostContent"""
    title = serializers.CharField(required=True, min_length=1, max_length=200)
    content = serializers.CharField(required=True, min_length=1)

    class Meta:
        model = PostContent
        fields = ['title', 'content']

    def validate_title(self, value):
        """Validate title is not empty after stripping"""
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty')
        return value

    def validate_content(self, value):
        """Validate content is not empty after stripping"""
        if not value.strip():
            raise serializers.ValidationError('Content cannot be empty')
        return value

    def create(self, validated_data):
        """Create post with current user"""
        user_id = self.context['request'].session.get('user_id')
        if not user_id:
            raise serializers.ValidationError('User must be authenticated')
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found')
        
        return PostContent.objects.create(
            user=user,
            **validated_data
        )


class PostContentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating PostContent"""
    title = serializers.CharField(required=False, min_length=1, max_length=200)
    content = serializers.CharField(required=False, min_length=1)

    class Meta:
        model = PostContent
        fields = ['title', 'content']

    def validate_title(self, value):
        """Validate title is not empty after stripping"""
        if value and not value.strip():
            raise serializers.ValidationError('Title cannot be empty')
        return value

    def validate_content(self, value):
        """Validate content is not empty after stripping"""
        if value and not value.strip():
            raise serializers.ValidationError('Content cannot be empty')
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model - for nested comments"""
    user = serializers.StringRelatedField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'comment', 'created_at', 'likes_count', 'dislikes_count', 'replies']
        read_only_fields = ['id', 'created_at', 'likes_count', 'dislikes_count']

    def get_replies(self, obj):
        """Recursively get child reviews"""
        children = obj.child_reviews.all().order_by('created_at')
        return ReviewSerializer(children, many=True).data


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating Review or Reply"""
    comment = serializers.CharField(required=True, min_length=1, max_length=500)
    review_id = serializers.IntegerField(required=False, allow_null=True)
    parent_reply_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_comment(self, value):
        """Validate comment is not empty"""
        if not value.strip():
            raise serializers.ValidationError('Comment cannot be empty')
        return value

    def validate(self, data):
        """Cross-field validation"""
        parent_reply_id = data.get('parent_reply_id')
        review_id = data.get('review_id')
        
        if parent_reply_id and not review_id:
            raise serializers.ValidationError('review_id is required when replying to a specific comment')
        
        return data


class PostStatsSerializer(serializers.ModelSerializer):
    """Serializer for PostStats"""
    class Meta:
        model = PostStats
        fields = ['likes_count', 'dislikes_count', 'favorites_count', 'views_count', 'shares_count', 'review_count']
        read_only_fields = fields


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Favorite"""
    post = PostContentSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['post', 'created_at']
        read_only_fields = fields