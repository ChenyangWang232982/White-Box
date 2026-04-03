import json
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import ValidationError as DRFValidationError
from white_box.utils import get_caller_name
from .models import PostContent, Review, PostStats
from users.models import User
from .utils.comment import create_review_or_reply
from .serializers import (
    PostContentSerializer,
    PostContentCreateSerializer,
    PostContentUpdateSerializer,
)


@require_http_methods(["POST"])
def create_post(request):
    """Create a new post"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)

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
                    'user_id': reply_obj.user.user_id,
                    'comment': reply_obj.comment,
                    'created_at': reply_obj.created_at.isoformat(),
                    'likes_count': reply_obj.likes_count,
                    'dislikes_count': reply_obj.dislikes_count,
                    'replies': [serialize_reply(child) for child in children_map.get(reply_obj.id, [])],
                }

            replies_data = [serialize_reply(reply) for reply in children_map.get(review.id, [])]

            reviews_data.append({
                'id': review.id,
                'user_id': review.user.user_id,
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

@require_http_methods(["PUT"])
def update_post(request, post_id):
    """Update an existing post"""
    try:
        post_content = PostContent.objects.get(post_id=post_id)
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


@require_http_methods(["DELETE"])
def delete_post(request, post_id):
    try:
        post_content = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            post_content.delete()
        return JsonResponse({'message': 'Post deleted successfully'}, status=200)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["GET"])
def list_posts(request, user_id):
    """List all posts by a user"""
    try:
        user = User.objects.get(user_id=user_id)
        posts = PostContent.objects.filter(user=user).order_by('-created_at')
        serializer = PostContentSerializer(posts, many=True)
        
        return JsonResponse({
            'message': 'Posts retrieved successfully',
            'posts': serializer.data
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["POST"])
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

@require_http_methods(["POST"])
def favorite_post(request, post_id):
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        user = User.objects.get(user_id=user_id)
        post_content = PostContent.objects.get(post_id=post_id)
        with transaction.atomic():
            user.favorites.add(post_content)
            post_stats, _ = PostStats.objects.get_or_create(post=post_content)
            post_stats.favorites_count += 1
            post_stats.save()
        return JsonResponse({'message': 'Post favorited successfully'}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["GET"])
def get_favorites(request):
    """Get all favorite posts for current user"""
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        user = User.objects.get(user_id=user_id)
        favorite_posts = user.favorites.all().order_by('-created_at')
        serializer = PostContentSerializer(favorite_posts, many=True)
        
        return JsonResponse({
            'message': 'Favorite posts retrieved successfully',
            'favorite_posts': serializer.data
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)


@require_http_methods(["POST"])
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

@require_http_methods(["POST"])
def report_post(request):
    raise NotImplementedError("Report post functionality is not implemented yet")

@require_http_methods(["POST"])
def share_post(request):
    raise NotImplementedError("Share post functionality is not implemented yet")


