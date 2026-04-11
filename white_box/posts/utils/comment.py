import json
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from posts.models import PostContent, Review, PostStats
from posts.serializers import ReviewCreateSerializer
from white_box.utils import get_caller_name


User = get_user_model()


def create_review_or_reply(request, post_id=None, review_id=None):
    """Create a review or reply with validation via serializer"""
    try:
        data = json.loads(request.body or "{}")
        
        # Validate input using serializer
        serializer = ReviewCreateSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=400)
        
        # Get user from session
        user_id = request.user.id if request.user.is_authenticated else request.session.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=401)
        
        validated_data = serializer.validated_data
        comment = validated_data.get('comment')
        effective_review_id = review_id if review_id is not None else validated_data.get('review_id')
        
        # Handle reply to a review or another reply
        if effective_review_id is not None:
            try:
                root_review = Review.objects.get(id=effective_review_id, parent_review__isnull=True)
            except Review.DoesNotExist:
                return JsonResponse({'error': 'Review not found'}, status=404)
            
            post = root_review.post
            if post_id is not None and post.post_id != post_id:
                return JsonResponse({'error': 'review_id does not belong to this post'}, status=400)
            
            parent_reply_id = validated_data.get('parent_reply_id')
            parent_review = root_review
            
            if parent_reply_id is not None:
                try:
                    parent_review = Review.objects.get(
                        id=parent_reply_id,
                        post=post,
                        root_review=root_review,
                        parent_review__isnull=False,
                    )
                except Review.DoesNotExist:
                    return JsonResponse({
                        'error': f'Parent reply not found in this review, error in {get_caller_name()}'
                    }, status=404)
            
            # Create reply
            reply = Review.objects.create(
                post=post,
                root_review=root_review,
                parent_review=parent_review,
                user=user,
                comment=comment,
            )
            
            # Update stats
            post_stats, _ = PostStats.objects.get_or_create(post=post)
            post_stats.review_count += 1
            post_stats.save()
            
            return JsonResponse({
                'message': 'Reply added successfully',
                'reply': {
                    'reply_id': reply.id,
                    'review_id': root_review.id,
                    'parent_reply_id': parent_reply_id,
                    'user_id': reply.user_id,
                    'comment': reply.comment,
                    'created_at': reply.created_at.isoformat(),
                    'likes_count': reply.likes_count,
                    'dislikes_count': reply.dislikes_count,
                }
            }, status=201)
        
        # Handle new review (no parent)
        if post_id is None:
            return JsonResponse({'error': 'post_id is required for creating a review'}, status=400)
        
        try:
            post = PostContent.objects.get(post_id=post_id)
        except PostContent.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)
        
        # Create review
        review = post.reviews.create(user=user, comment=comment)
        
        # Update stats
        post_stats, _ = PostStats.objects.get_or_create(post=post)
        post_stats.review_count += 1
        post_stats.save()
        
        return JsonResponse({
            'message': 'Review added successfully',
            'review': {
                'review_id': review.id,
                'user_id': review.user_id,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'likes_count': review.likes_count,
                'dislikes_count': review.dislikes_count,
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)} in {get_caller_name()}'
        }, status=500)