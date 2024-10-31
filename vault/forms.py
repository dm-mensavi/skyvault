from django import forms
from .models import File, Folder

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['uploaded_file']

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
