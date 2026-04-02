from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError
from users.models import User
import json
from white_box.utils import get_caller_name


@require_http_methods(["POST"])
def register(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return JsonResponse({'success': False, 'message': 'Username, password, and email are required'}, status=400)
        
        user = User.objects.create(
            username=username,
            password=make_password(password),
            email=email
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'user_id': user.user_id
        }, status=201)
    
    except IntegrityError:
        return JsonResponse({'success': False, 'message': 'Username or email already exists'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["POST"])
def login(request):
    """User login"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'success': False, 'message': 'Username and password are required'}, status=400)
        
        user = User.objects.get(username=username)
        
        if not check_password(password, user.password):
            return JsonResponse({'success': False, 'message': 'Username or password is incorrect'}, status=401)
        
        if not user.is_active:
            return JsonResponse({'success': False, 'message': 'Account is disabled'}, status=403)
        
        request.session['user_id'] = user.user_id
        request.session['username'] = user.username
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'user_id': user.user_id,
            'username': user.username
        }, status=200)
    
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Username or password is incorrect'}, status=401)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
@require_http_methods(["POST"])
def forget_password(request):
    raise NotImplementedError("Forget password functionality is not implemented yet")

@require_http_methods(["POST"])
def verification_code(request):
    raise NotImplementedError("Verification code functionality is not implemented yet")


@require_http_methods(["POST"])
def login_with_verification_code(request):
    raise NotImplementedError("Login with verification code functionality is not implemented yet")

