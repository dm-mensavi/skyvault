from .models import File
from django.contrib.auth.decorators import login_required

@login_required
def storage_info(request):
    user_files = File.objects.filter(user=request.user)
    total_storage = sum(file.size for file in user_files) / (1024 * 1024)  # Convert bytes to MB
    max_storage = 100  # 100 MB limit
    used_percentage = (total_storage / max_storage) * 100 if max_storage else 0

    return {
        'total_storage': total_storage,
        'max_storage': max_storage,
        'used_percentage': used_percentage,
    }
