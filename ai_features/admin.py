from django.contrib import admin
from .models import FileAnalysis, StorageInsight


@admin.register(FileAnalysis)
class FileAnalysisAdmin(admin.ModelAdmin):
    list_display = ("file", "status", "suggested_folder", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("file__name", "summary", "tags")


@admin.register(StorageInsight)
class StorageInsightAdmin(admin.ModelAdmin):
    list_display = ("user", "generated_at")
    search_fields = ("user__username", "insight")
    readonly_fields = ("generated_at", "stats_snapshot")

