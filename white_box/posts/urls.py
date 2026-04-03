from django.urls import path
from posts import views
app_name = 'posts'
urlpatterns = [
    path(f'create_post/', views.create_post, name='create_post'),
    path(f'get_post/<str:post_id>/', views.get_post, name='get_post'),
    path(f'update_post/<str:post_id>/', views.update_post, name='update_post'),
    path(f'delete_post/<str:post_id>/', views.delete_post, name='delete_post'),
    path(f'list_posts/<str:user_id>/', views.list_posts, name='list_posts'),
    path(f'comment_post/<str:post_id>/', views.comment_post, name='comment_post'),
    path(f'like_post/<str:post_id>/', views.like_post, name='like_post'),
    path(f'favorite_post/<str:post_id>/', views.favorite_post, name='favorite_post'),
    path(f'get_favorites/<str:user_id>/', views.get_favorites, name='get_favorites'),
    

]