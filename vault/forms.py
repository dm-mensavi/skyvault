from django import forms
from .models import File, Folder

AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "m4r", "aiff", "opus", "mid", "midi"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v", "3gp", "ogv"}
DISALLOWED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def validate_not_audio_or_video(file):
    ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
    content_type = getattr(file, 'content_type', '') or ''
    if ext in DISALLOWED_EXTENSIONS or content_type.startswith(('audio/', 'video/')):
        raise forms.ValidationError("Audio and video files are not allowed.")


class FileUploadForm(forms.ModelForm):
    uploaded_file = forms.FileField(validators=[validate_not_audio_or_video])

    class Meta:
        model = File
        fields = ['uploaded_file']

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
