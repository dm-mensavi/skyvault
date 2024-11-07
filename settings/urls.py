# settings/urls.py
from django.urls import path
from accounts import views as account_views
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile_view'),  # Profile page view
    path('profile/update/', views.update_profile_view, name='update_profile_view'),
    path('logout/', account_views.logout_view, name='logout_view'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
