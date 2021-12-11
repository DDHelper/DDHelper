from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.list_dynamic, name='list_dynamics'),
    path("dsinfo/", views.DynamicSyncInfoListView.as_view()),
    path("dsinfo/latest/", views.DynamicSyncInfoLatestDetailView.as_view()),
    path("dsinfo/<int:pk>/", views.DynamicSyncInfoDetailView.as_view())
]

