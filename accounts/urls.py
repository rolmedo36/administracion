from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('users/', views.user_list, name='user_list'),
    path('users/crear/', views.user_create, name='user_create'),
    path('users/<int:pk>/editar/', views.user_update, name='user_update'),
    path('users/<int:pk>/eliminar/', views.user_delete, name='user_delete'),
]
