from django.db import models
from django.contrib.auth.models import User
import os
from django.db import models
from django.contrib.auth.models import User


def user_directory_path(instance, filename):
    # This function sets the path for uploaded files as `media/user_<id>/<filename>`
    return f'user_{instance.user.id}/{filename}'

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    trashed = models.BooleanField(default=False)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, blank=True, null=True, related_name='files')
    name = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to=user_directory_path)
    size = models.PositiveIntegerField()  # Size in bytes
    trashed = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, related_name='shared_files', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    starred = models.BooleanField(default=False)

    def __str__(self):
        return self.name