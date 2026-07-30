from settings.models import UserProfile

def storage_info(request):
    if not request.user.is_authenticated:
        return {
            "total_storage": 0,
            "max_storage": 100,
            "used_percentage": 0,
        }

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    total_storage = profile.used_space / (1024 * 1024)
    max_storage = profile.MAX_STORAGE_LIMIT / (1024 * 1024)
    used_percentage = min((total_storage / max_storage) * 100 if max_storage else 0, 100)

    return {
        "total_storage": total_storage,
        "max_storage": max_storage,
        "used_percentage": used_percentage,
    }


