import json
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError as DRFValidationError
from white_box.utils import get_caller_name
from .models import PostContent, Review, PostStats, Favorite
from .utils.comment import create_review_or_reply
from .serializers import (
    PostContentSerializer,
    PostContentCreateSerializer,
    PostContentUpdateSerializer,
    ReportSerializer
)
from users.utils.permissions import can_manage_post, login_required_json


User = get_user_model()

"""
Request body for create_post:
{
    "title": "Post title",
    "content": "Post content"
}
"""
@require_http_methods(["POST"])
@login_required_json
def create_post(request):
    """Create a new post"""
    try:
        data = json.loads(request.body or "{}")
        serializer = PostContentCreateSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            post = serializer.save()
            return JsonResponse({
                'message': 'Post created successfully',
                'post': {
                    'post_id': post.post_id,
                    'title': post.title,
                    'content': post.content
                }
            }, status=201)
        else:
            return JsonResponse({
                'error': 'Post creation failed',
                'details': serializer.errors
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except DRFValidationError as e:
        return JsonResponse({'error': 'Validation failed', 'details': e.detail}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)} in {get_caller_name()}'}, status=500)
    
"""
Request body for get_post:
No request body needed, just need post_id in the URL to identify which post we want to retrieve"""
@require_http_methods(["GET"])
def get_post(request, post_id):
    try:
        post_content = PostContent.objects.prefetch_related('reviews__user').get(post_id=post_id) #prefetch_related('reviews__user')可以一次性获取与PostContent相关的所有Review对象以及每个Review对象关联的User对象，避免在后续访问reviews和user时产生额外的数据库查询，从而提高性能。
        all_comments = list(post_content.reviews.select_related('user').all().order_by('created_at'))
        reviews = [comment for comment in all_comments if comment.parent_review_id is None]
        reviews.sort(key=lambda comment: comment.created_at, reverse=True)

        children_map = {}
        for comment in all_comments:
            if comment.parent_review_id is not None:
                children_map.setdefault(comment.parent_review_id, []).append(comment)

        reviews_data = []
        for review in reviews:
            def serialize_reply(reply_obj):
                return {
                    'id': reply_obj.id,
                    'user_id': reply_obj.user_id,
                    'comment': reply_obj.comment,
                    'created_at': reply_obj.created_at.isoformat(),
                    'likes_count': reply_obj.likes_count,
                    'dislikes_count': reply_obj.dislikes_count,
                    'replies': [serialize_reply(child) for child in children_map.get(reply_obj.id, [])],
                }

            replies_data = [serialize_reply(reply) for reply in children_map.get(review.id, [])]

            reviews_data.append({
                'id': review.id,
                'user_id': review.user_id,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'likes_count': review.likes_count,
                'dislikes_count': review.dislikes_count,
                'replies': replies_data,
            })
        
        return JsonResponse({
            'message': 'Post retrieved successfully',
            'post': {
                'post_id': post_content.post_id,
                'title': post_content.title,
                'content': post_content.content,
                'created_at': post_content.created_at.isoformat(),
                'updated_at': post_content.updated_at.isoformat(),
                'reviews': reviews_data,
            }
        }, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for update_post:
{
    "title": "Updated title", (optional)
    "content": "Updated content" (optional)
}
"""
@require_http_methods(["PUT"])
@login_required_json
def update_post(request, post_id):
    """Update an existing post"""
    try:
        post_content = PostContent.objects.get(post_id=post_id)
        if not can_manage_post(request.user, post_content):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        data = json.loads(request.body or "{}")
        serializer = PostContentUpdateSerializer(instance=post_content, data=data, partial=True)
        
        if serializer.is_valid():
            post = serializer.save()
            return JsonResponse({
                'message': 'Post updated successfully',
                'post': {
                    'post_id': post.post_id,
                    'title': post.title,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'updated_at': post.updated_at.isoformat()
                }
            }, status=200)
        else:
            return JsonResponse({
                'error': 'Post update failed',
                'details': serializer.errors
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)

"""
Request body for delete_post:
No request body needed, just need post_id in the URL to identify which post we want to delete
"""
@require_http_methods(["DELETE"])
@login_required_json
def delete_post(request, post_id):
    try:
        post_content = PostContent.objects.get(post_id=post_id)
        if not can_manage_post(request.user, post_content):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        with transaction.atomic():
            post_content.delete()
        return JsonResponse({'message': 'Post deleted successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for list_posts:
No request body needed, just need user_id in the URL to identify which user's posts we want to retrieve"""
@require_http_methods(["GET"])
def list_posts(request, user_id):
    """List all posts by a user"""
    try:
        user = User.objects.get(pk=user_id)
        posts = PostContent.objects.filter(user=user).order_by('-created_at')
        serializer = PostContentSerializer(posts, many=True)
        
        return JsonResponse({
            'message': 'Posts retrieved successfully',
            'posts': serializer.data
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)
"""
Request body for like_post:
No request body needed, just need user session to identify the user who is liking the post
"""
@require_http_methods(["POST"])
@login_required_json
def like_post(request, post_id):
    try:
        post_content = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            post_stats, _ = PostStats.objects.get_or_create(post=post_content) # 确保 PostStats 存在
            post_stats.likes_count += 1
            post_stats.save()
        return JsonResponse({'message': 'Post liked successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for favorite_post:
No request body needed, just need user session to identify the user who is favoriting the post"""
@require_http_methods(["POST"])
@login_required_json
def favorite_post(request, post_id):
    try:
        user = request.user
        post_content = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            favorite, created = Favorite.objects.get_or_create(user=user, post=post_content)
            post_stats, _ = PostStats.objects.get_or_create(post=post_content)
            if created:
                post_stats.favorites_count += 1
                post_stats.save()
        return JsonResponse({'message': 'Post favorited successfully'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for get_favorites:
No request body needed, just need user session to identify the user whose favorites we want to retrieve
"""
@require_http_methods(["GET"])
@login_required_json
def get_favorites(request):
    """Get all favorite posts for current user"""
    try:
        user = request.user
        favorite_posts = PostContent.objects.filter(favorites__user=user).order_by('-created_at')
        serializer = PostContentSerializer(favorite_posts, many=True)
        
        return JsonResponse({
            'message': 'Favorite posts retrieved successfully',
            'favorite_posts': serializer.data
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

"""
Request body for comment_post:
{
    "comment": "This is a comment",
    "parent_reply_id": 123 (optional, required if review_id is provided),
    "review_id": 456 (optional, required if parent_review_id is provided)
}
"""
@require_http_methods(["POST"])
@login_required_json
def comment_post(request, post_id):
    try:
        return create_review_or_reply(request, post_id=post_id)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
    except Review.DoesNotExist:
        return JsonResponse({'error': f'Review not found, error in {get_caller_name()}'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)
"""
Request body for report_post:
{
    "reason": "Inappropriate content"
}
"""
@require_http_methods(["POST"]) #Report a post
@login_required_json
def report_post(request, post_id):
    try:
         serializer = ReportSerializer(data=json.loads(request.body or "{}"), context={'request': request, 'view': request.resolver_match})
         if serializer.is_valid(raise_exception=True):
            serializer.save()
            post = PostContent.objects.get(post_id=post_id)
            with transaction.atomic():
                post.reports_count += 1
                post.save()
            return JsonResponse({'message': 'Post reported successfully'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except DRFValidationError as e:
        return JsonResponse({'error': 'Validation failed', 'details': e.detail}, status=400)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

"""
Request body for share_post:
No request body needed, just need post_id in the URL to identify which post we want to share
"""
@require_http_methods(["POST"])
@login_required_json
def share_post(request, post_id):
    try:
        post = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            post.stats.shares_count += 1
            post.stats.save()
        return JsonResponse({'message': 'Post shared successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for unlike_post:
No request body needed, just need user session to identify the user who is unliking the post
"""
@require_http_methods(["POST"])
@login_required_json
def unlike_post(request, post_id):
    try:
        post_content = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            post_stats, _ = PostStats.objects.get_or_create(post=post_content) # 确保 PostStats 存在
            post_stats.dislikes_count -= 1
            post_stats.save()
        return JsonResponse({'message': 'Post unliked successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
"""
Request body for unfavorite_post:
No request body needed, just need user session to identify the user who is unfavoriting the post
"""  
@require_http_methods(["POST"])
@login_required_json
def unfavorite_post(request, post_id):
    try:
        post = PostContent.objects.get(post_id=post_id)
        user = request.user
        with transaction.atomic():
            deleted_count, _ = Favorite.objects.filter(user=user, post=post).delete()
            post_stats, _ = PostStats.objects.get_or_create(post=post)
            if deleted_count > 0 and post_stats.favorites_count > 0:
                post_stats.favorites_count -= 1
                post_stats.save()
        return JsonResponse({'message': 'Post unfavorited successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)
"""
Request body for search_posts:
{
    "keyword": "search keyword"
}
"""
@require_http_methods(["POST"])
def search_posts(request):
    try:
        data = json.loads(request.body or "{}")
        keyword = data.get('keyword', '')
        if not keyword:
            return JsonResponse({'error': 'Keyword is required for searching'}, status=400)
        
        posts = PostContent.objects.filter(title__icontains=keyword).order_by('-created_at')
        serializer = PostContentSerializer(posts, many=True)
        
        return JsonResponse({
            'message': 'Search completed successfully',
            'posts': serializer.data
        }, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)