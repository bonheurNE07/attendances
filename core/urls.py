from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_view, profile_view, register_view, home, logout_view

app_name = 'core'

urlpatterns = [
    path('', login_view, name='login'),  # Root URL redirects to login
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('home/', home, name='home'),
    path('logout/', logout_view, name='logout'),  
]