# settings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile_view'),  # Profile page view
    path('profile/update/', views.update_profile_view, name='update_profile_view'),
]
