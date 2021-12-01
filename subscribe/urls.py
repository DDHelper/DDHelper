from django.urls import path

from . import views

urlpatterns = [
    path('search/', views.search, name='search'),
    path('subscribe/', views.subscribe, name='member_subscribe'),
    path('group_list/', views.group_list, name='group_list'),
    path('group/members/', views.group_members, name='group_members'),
    path('group/add/', views.add_group, name='add_group'),
    path('group/update/', views.update_group, name='update_group'),
    path('group/delete/', views.delete_group, name='delete_group'),
    path('member/move/', views.member_move, name='member_move')
]
