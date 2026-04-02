from django.urls import path
from users import views
import dotenv
app_name = 'users'
BASEURL = dotenv.get_key('.env', 'BASEURL') or 'api'
urlpatterns = [
    path(f'{BASEURL}/register/', views.register, name='register'),
    path(f'{BASEURL}/login/', views.login, name='login'),
    path(f'{BASEURL}/forget_password/', views.forget_password, name='forget_password'),
    path(f'{BASEURL}/login_with_verification_code/', views.login_with_verification_code, name='login_with_verification_code'),
]
