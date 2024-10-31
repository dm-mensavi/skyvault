from django.urls import path
from . import views

urlpatterns = [
    path("", views.vault_home, name="vault_home"),
    path('upload/', views.upload_file, name='upload_file'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path("trash/", views.trash_view, name="trash_view"),
    path("shared/", views.shared_view, name="shared_view"),
    path("search/", views.search_view, name="search_view"),
    path("recent/", views.recent_files, name="recent_files"),
    path("starred/", views.starred_files, name="starred_files"),
    path("storage/", views.storage_info, name="storage_info"),
]
