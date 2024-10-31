# settings/models.py

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    used_space = models.PositiveIntegerField(default=0)  # Store used space in bytes
    bio = models.TextField(blank=True, null=True)  # Add bio field
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)  # Add profile picture field

    MAX_STORAGE_LIMIT = 100 * 1024 * 1024  # 100 MB limit

    def is_storage_exceeded(self, additional_size=0):
        """Check if adding additional_size would exceed storage limit."""
        return (self.used_space + additional_size) > self.MAX_STORAGE_LIMIT

    def __str__(self):
        return self.user.username
