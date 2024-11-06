from django.urls import path
from . import views

urlpatterns = [
    path("", views.vault_home, name="vault_home"),
    path('upload/', views.upload_file, name='upload_file'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('folder/<int:folder_id>/', views.view_folder, name='view_folder'),
    path('open-file/<int:file_id>/', views.open_file, name='open_file'),
    path('paste/', views.paste, name='paste'),
    path("trash/", views.trash_view, name="trash_view"),
    path("shared/", views.shared_view, name="shared_view"),
    path("search/", views.search_view, name="search_view"),
    path("recent/", views.recent_files, name="recent_files"),
    path("starred/", views.starred_files, name="starred_files"),
    path("storage/", views.storage_info, name="storage_info"),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('delete-folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('restore/<str:item_type>/<int:item_id>/', views.restore_item, name='restore_item'),
    path('delete-permanent/<str:item_type>/<int:item_id>/', views.delete_permanent_item, name='delete_permanent_item'),

]
