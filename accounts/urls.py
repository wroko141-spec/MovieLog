from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.MovieLogLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot/', views.forgot_password, name='forgot_password'),
    path('reset/<str:token>/', views.reset_password, name='reset_password'),
]
