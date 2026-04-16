from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, NotAuthenticated
from django.contrib.auth import get_user_model
from .models import PostContent, PostStats, Report, Review, Favorite


User = get_user_model()


class ConflictError(APIException):
    status_code = 409
    default_detail = 'Conflict'
    default_code = 'conflict'


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
        request = self.context['request']
        user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')
        if not user_id:
            raise serializers.ValidationError('User must be authenticated')
        try:
            user = User.objects.get(pk=user_id)
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

class ReportSerializer(serializers.ModelSerializer):
    """Serializer for creating Report"""
    class Meta:
        model = Report
        fields = ['reason', 'user', 'post']
        read_only_fields = ['user', 'post']

    def validate_reason(self, value):
        """Validate reason is not empty."""
        if not value.strip():
            raise serializers.ValidationError('Reason cannot be empty')
        return value

    def validate(self, attrs):
        request = self.context['request']
        user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')
        if not user_id:
            raise NotAuthenticated('User must be authenticated')

        post_id = self.context.get('post_id')
        if not post_id:
            raise serializers.ValidationError('post_id is required in URL')

        user = User.objects.filter(pk=user_id).first()
        if user is None:
            raise NotAuthenticated('User not found')

        post = PostContent.objects.filter(post_id=post_id).first()
        if post is None:
            raise NotFound('Post not found')

        if Report.objects.filter(user=user, post=post).exists():
            raise ConflictError('You have already reported this post')

        attrs['user'] = user
        attrs['post'] = post
        return attrs

    def create(self, validated_data):
        """Create report using validated user/post from validate()."""
        return Report.objects.create(
            user=validated_data['user'],
            post=validated_data['post'],
            reason=validated_data['reason'] #validated_data中已经包含了经过验证的user和post对象，因此直接使用它们来创建Report实例，而不需要再次从数据库中查询。这种方式更高效，因为我们已经在validate()方法中确保了user和post的有效性，并且避免了不必要的数据库查询。
        )