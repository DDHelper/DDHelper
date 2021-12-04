from django.urls import path

from . import views

urlpatterns = [
    path('showtimeline/', views.show_timeline, name='timeline'),
]