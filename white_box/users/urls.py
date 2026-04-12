from django.urls import path
from users import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView #TokenRefreshView是一个视图类，用于处理JWT令牌的刷新请求。当客户端发送一个包含有效刷新令牌的POST请求到这个视图时，视图会验证刷新令牌的有效性，如果有效，则生成一个新的访问令牌并返回给客户端。TokenVerifyView是另一个视图类，用于验证JWT令牌的有效性。当客户端发送一个包含访问令牌的POST请求到这个视图时，视图会验证访问令牌是否有效，如果有效，则返回一个成功响应；如果无效，则返回一个错误响应。这两个视图通常用于实现基于JWT的认证机制，允许客户端在访问受保护资源时使用访问令牌，并在需要时刷新访问令牌以保持会话的持续性。
app_name = 'users'
urlpatterns = [
    path(f'register/', views.register, name='register'),
    path(f'login/', views.login, name='login'),
    path(f'token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path(f'token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path(f'forget_password/', views.forget_password, name='forget_password'),
    path(f'verification_code/', views.verification_code, name='verification_code'),
    path(f'login_with_verification_code/', views.login_with_verification_code, name='login_with_verification_code'),
]
