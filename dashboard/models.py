from django.db import models

class File(models.Model):
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    size = models.IntegerField()  # in bytes
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
