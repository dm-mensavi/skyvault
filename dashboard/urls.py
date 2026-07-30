# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('file-type-distribution/', views.file_type_distribution, name='file_type_distribution'),
    path('storage-usage-over-time/', views.storage_usage_over_time, name='storage_usage_over_time'),
    path('ai-insight/', views.ai_insight, name='dashboard_ai_insight'),
]
