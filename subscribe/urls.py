from django.urls import path

from . import views

urlpatterns = [
    path('search/', views.search, name='search'),
    path('showlist/', views.showlist, name='showlist'),
    path('membersubscribe/', views.mem_subscribe, name='mem_subscribe'),
    path('addgroup/', views.add_group, name='add_group'),
    path('updategroup/', views.update_group, name='update_group'),
    path('membermove/', views.mem_move, name='mem_move')
]
