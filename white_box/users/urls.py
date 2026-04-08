from django.urls import path
from users import views
app_name = 'users'
urlpatterns = [
    path(f'register/', views.register, name='register'),
    path(f'login/', views.login, name='login'),
    path(f'forget_password/', views.forget_password, name='forget_password'),
    path(f'verification_code/', views.verification_code, name='verification_code'),
    path(f'login_with_verification_code/', views.login_with_verification_code, name='login_with_verification_code'),
]
