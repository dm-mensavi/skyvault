from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from .views import home_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("vault/", include("vault.urls")),
    path("settings/", include("settings.urls")),
    path("notifications/", include("notifications.urls")),
    path("", home_view, name="home"),
]
