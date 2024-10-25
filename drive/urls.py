from django.urls import path
from .views import profile_view
from .views import profile_update_view

urlpatterns = [
    path('profile/', profile_view, name='profile'),
    path('profile/update/', profile_update_view, name='profile_update'),
]
