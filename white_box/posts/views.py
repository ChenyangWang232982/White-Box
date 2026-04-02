import uuid
import json
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from white_box.utils import get_caller_name
from .models import PostContent, Review, Reply, PostStats
from users.models import User
# Create your views here.
@require_http_methods(["POST"])
def create_post(request):
    try:
        data = json.loads(request.body or "{}")
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return JsonResponse({'error': 'Title and content are required'}, status=400)
        
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)

        user = User.objects.get(user_id=user_id)
        
        with transaction.atomic(): # 确保数据一致性
            post_content = PostContent.objects.create(
                user=user,
                title=title,
                content=content
            )
        
        return JsonResponse({
            'message': 'Post created successfully',
            'post': {
                'post_id': post_content.post_id,
                'title': post_content.title,
                'content': post_content.content
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=401)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)} in {get_caller_name()}'}, status=500)
    

@require_http_methods(["GET"])
def get_post(request, post_id):
    try:
        post_content = PostContent.objects.prefetch_related(
            'reviews__replies'
        ).get(post_id=post_id)
        reviews = post_content.reviews.all().order_by('-created_at')

        reviews_data = []
        for review in reviews:
            all_replies = list(review.replies.select_related('user').all().order_by('created_at')) # 获取所有回复并按创建时间排序
            children_map = {} # parent_reply_id -> list of child replies
            for reply in all_replies: # 构建父子关系映射
                children_map.setdefault(reply.parent_reply_id, []).append(reply) # 将回复按照 parent_reply_id 分类，None 表示一级回复

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

            replies_data = [serialize_reply(reply) for reply in children_map.get(None, [])]

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
    try:
        data = json.loads(request.body or "{}")
        post_content = PostContent.objects.get(post_id=post_id)
        revised_content = data.get('content')
        revised_title = data.get('title')
        if not revised_title: 
            revised_title = post_content.title
        if not revised_content:
            revised_content = post_content.content
        with transaction.atomic():
            post_content.title = revised_title
            post_content.content = revised_content
            post_content.save()
        return JsonResponse({
            'message': 'Post updated successfully',
            'post': {
                'post_id': post_content.post_id,
                'title': post_content.title,
                'content': post_content.content,
                'created_at': post_content.created_at.isoformat(),
                'updated_at': post_content.updated_at.isoformat()
            }
        }, status=200)
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
    try:
        user = User.objects.get(user_id=user_id)
        posts = PostContent.objects.filter(user=user).order_by('-created_at')
        posts_data = [{
            'post_id': post.post_id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat()
        } for post in posts]
        return JsonResponse({
            'message': 'Posts retrieved successfully',
            'posts': posts_data
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
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        user = User.objects.get(user_id=user_id)
        favorite_posts = user.favorites.all().order_by('-created_at')
        posts_data = [{
            'post_id': post.post_id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat()
        } for post in favorite_posts]
        return JsonResponse({
            'message': 'Favorite posts retrieved successfully',
            'favorite_posts': posts_data
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["POST"])
def review_post(request, post_id):
    try:
        post = PostContent.objects.get(post_id=post_id)
        post_stats, _ = PostStats.objects.get_or_create(post=post)
        data = json.loads(request.body or "{}")
        comment = data.get('comment')
        if not comment:
            return JsonResponse({'error': 'Comment is required'}, status=400)

        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        user = User.objects.get(user_id=user_id)

        review = post.reviews.create(user=user, comment=comment)
        post_stats.review_count += 1
        post_stats.save()
        return JsonResponse({
            'message': 'Review added successfully',
            'review': {
                'review_id': review.id,
                'user_id': review.user.user_id,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'likes_count': review.likes_count,
                'dislikes_count': review.dislikes_count,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except PostContent.DoesNotExist:
        return JsonResponse({'error': f'Post not found, error in {get_caller_name()}'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["POST"])
def reply_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        data = json.loads(request.body or "{}")
        comment = data.get('comment')
        parent_reply_id = data.get('parent_reply_id')
        post = review.post
        post_stats, _ = PostStats.objects.get_or_create(post=post)

        if not comment:
            return JsonResponse({'error': 'Comment is required'}, status=400)

        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        user = User.objects.get(user_id=user_id)

        parent_reply = None
        if parent_reply_id is not None:
            parent_reply = Reply.objects.get(id=parent_reply_id, review=review)

        reply = Reply.objects.create(
            review=review,
            parent_reply=parent_reply,
            user=user,
            comment=comment,
        )
        post_stats.review_count += 1
        post_stats.save()

        return JsonResponse({
            'message': 'Reply added successfully',
            'reply': {
                'reply_id': reply.id,
                'review_id': reply.review_id,
                'parent_reply_id': reply.parent_reply_id,
                'user_id': reply.user.user_id,
                'comment': reply.comment,
                'created_at': reply.created_at.isoformat(),
                'likes_count': reply.likes_count,
                'dislikes_count': reply.dislikes_count,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Review.DoesNotExist:
        return JsonResponse({'error': f'Review not found, error in {get_caller_name()}'}, status=404)
    except Reply.DoesNotExist:
        return JsonResponse({'error': f'Parent reply not found in this review, error in {get_caller_name()}'}, status=404)
    except User.DoesNotExist:
        return JsonResponse({'error': f'User not found, error in {get_caller_name()}'}, status=404)

@require_http_methods(["POST"])
def report_post(request):
    raise NotImplementedError("Report post functionality is not implemented yet")

@require_http_methods(["POST"])
def share_post(request):
    raise NotImplementedError("Share post functionality is not implemented yet")


