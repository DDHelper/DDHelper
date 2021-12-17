from django.urls import path

from . import views

urlpatterns = [
    path('list', views.show_timeline, name='timeline'),
]