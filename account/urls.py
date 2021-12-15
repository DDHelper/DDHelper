from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('user_info', views.user_info, name='user_info'),
    path('register/', views.register, name='register'),
    path('send_pin/', views.send_pin, name='send_pin'),
    path('verify_pin', views.verify_pin, name='verify_pin')
]
