from django.http import JsonResponse
from django.contrib.auth import login as auth_login
from django.views.decorators.http import require_http_methods
from users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    VerificationCodeRequestSerializer,
    LoginWithVerificationCodeSerializer,
    ForgetPasswordSerializer,
)
import json
from white_box.utils import get_caller_name


@require_http_methods(["POST"])
def register(request):
    """Register a new user"""
    try:
        data = json.loads(request.body)
        serializer = RegisterSerializer(data=data)
        
        if serializer.is_valid(): #is_valid()方法会调用serializer中的validate_username、validate_email和validate方法来验证输入的数据是否符合要求，如果验证通过，is_valid()返回True，并且可以通过serializer.validated_data获取验证后的数据；如果验证失败，is_valid()返回False，并且可以通过serializer.errors获取错误信息。
            user = serializer.save() #save()方法会调用serializer中的create方法来创建一个新的User对象，并将验证后的数据传递给create方法，create方法会返回创建的User对象。
            return JsonResponse({
                'success': True,
                'message': 'Registration successful',
                'user_id': user.id
            }, status=201)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Registration failed',
                'errors': serializer.errors
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["POST"])
def login(request):
    """User login"""
    try:
        data = json.loads(request.body)
        serializer = LoginSerializer(data=data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username
            }, status=200)
        else:
            errors = serializer.errors
            is_disabled = 'Account is disabled' in str(errors)
            return JsonResponse({
                'success': False,
                'message': 'Account is disabled' if is_disabled else 'Login failed',
                'errors': errors
            }, status=403 if is_disabled else 401)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

"""
request body:
{
    "email": "testuser@example.com"
    "code": "123456",
    "new_password": "newpassword123"
    "password_confirm": "newpassword123"
}
"""
@require_http_methods(["POST"])
def forget_password(request):
    try:
        data = json.loads(request.body)
        serializer = ForgetPasswordSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True, 'message': 'Password reset successful'}, status=200)
        return JsonResponse({'success': False, 'message': 'Password reset failed', 'errors': serializer.errors}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

"""
request body:
{
    "email": "testuser@example.com",
    "purpose": "login"  # or "reset_password"
}
"""
@require_http_methods(["POST"])
def verification_code(request):
    try:
        data = json.loads(request.body)
        serializer = VerificationCodeRequestSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'success': True, 'message': 'Verification code sent'}, status=200)
        return JsonResponse({'success': False, 'message': 'Failed to send verification code', 'errors': serializer.errors}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

"""
request body:
{
    "email": "testuser@example.com",
    "code": "123456"
}
"""

@require_http_methods(["POST"])
def login_with_verification_code(request):
    try:
        data = json.loads(request.body)
        serializer = LoginWithVerificationCodeSerializer(data=data)

        if serializer.is_valid():
            result = serializer.save()
            user = result['user']
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['username'] = user.username

            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user_id': user.id,
                'username': user.username,
            }, status=200)

        return JsonResponse({
            'success': False,
            'message': 'Login failed',
            'errors': serializer.errors,
        }, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Error in {get_caller_name()}: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

