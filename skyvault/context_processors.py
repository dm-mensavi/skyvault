from django.contrib.auth.decorators import login_required
from .models import UserProfile

def storage_info(request):
    """
    Injects storage information globally into all templates.
    """
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            used_mb = profile.used_space / (1024 * 1024)
            max_mb = profile.storage_limit / (1024 * 1024)
            percentage = (used_mb / max_mb) * 100 if max_mb > 0 else 0
            return {
                'used_storage': used_mb,
                'max_storage': max_mb,
                'total_storage': used_mb,
                'used_percentage': percentage,
                'user_profile': profile,
            }
        except UserProfile.DoesNotExist:
            return {
                'used_storage': 0,
                'max_storage': 100,
                'total_storage': 0,
                'used_percentage': 0,
                'user_profile': None,
            }
    return {
        'used_storage': 0,
        'max_storage': 100,
        'total_storage': 0,
        'used_percentage': 0,
        'user_profile': None,
    }
