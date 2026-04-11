from functools import wraps

from django.http import JsonResponse


def login_required_json(view_func): #这是一个装饰器函数，用于保护视图函数，确保只有经过身份验证的用户才能访问该视图。当一个视图函数被这个装饰器包装时，如果请求的用户没有通过身份验证，装饰器会返回一个JSON响应，提示用户必须进行身份验证，并且HTTP状态码为401（未授权）。如果用户已经通过身份验证，装饰器会调用原始的视图函数并返回其结果。
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated: 
            return JsonResponse({'error': 'User must be authenticated'}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper


def in_groups(user, group_names):
    if not group_names:
        return False
    return user.groups.filter(name__in=group_names).exists()


def has_any_perm(user, perm_codes): #perm_codes是一个权限代码列表，例如['posts.change_postcontent', 'posts.delete_postcontent']，表示用户需要至少拥有其中一个权限才能执行某个操作。如果perm_codes列表为空，函数直接返回False，表示没有任何权限要求；如果perm_codes列表不为空，函数会检查用户是否拥有列表中的任意一个权限，如果有，则返回True，否则返回False。
    if not perm_codes:
        return False
    return any(user.has_perm(code) for code in perm_codes)


def can_manage_post(user, post): #这个函数用于判断一个用户是否有权限管理（编辑或删除）一个帖子。它首先检查用户是否经过身份验证，如果没有，则返回False。接着，它检查用户是否是超级用户或管理员，如果是，则返回True。然后，它检查用户是否是帖子的作者，如果是，则返回True。接下来，它检查用户是否属于admin或moderator组，如果是，则返回True。最后，它检查用户是否拥有posts.change_postcontent或posts.delete_postcontent权限，如果有其中之一，则返回True；如果没有任何条件满足，则返回False。
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if post.user_id == user.id:
        return True
    if in_groups(user, ['admin', 'moderator']):
        return True
    return has_any_perm(user, ['posts.change_postcontent', 'posts.delete_postcontent'])
