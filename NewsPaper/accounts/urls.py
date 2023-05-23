from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from .views import BaseRegisterView, IndexView, upgrade_me

urlpatterns = [
    path('login/',
         LoginView.as_view(template_name='news/login.html'),
         name='login'),
    path('logout/',
         LogoutView.as_view(template_name='news/logout.html'),
         name='logout'),
    path('signup/',
         BaseRegisterView.as_view(template_name='news/signup.html'),
         name='signup'),
    path('upgrade/', upgrade_me, name='upgrade'),
]