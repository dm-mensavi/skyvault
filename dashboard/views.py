from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from ai_features.services.insights import generate_storage_insight
from vault.models import File


# Render the dashboard page
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


# View for file type distribution
def file_type_distribution(request):
    file_type_counts = (
        File.objects.filter(trashed=False, user=request.user)
        .values('uploaded_file')
        .annotate(count=Count('id'))
    )
    
    type_counts = {
        'Documents': 0,
        'Images': 0,
        'Videos': 0,
        'Audio': 0,
        'Others': 0,
    }

    for item in file_type_counts:
        file_name = item['uploaded_file']
        count = item['count']
        if file_name.endswith(('.pdf', '.doc', '.docx', '.txt')):
            type_counts['Documents'] += count
        elif file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            type_counts['Images'] += count
        elif file_name.endswith(('.mp4', '.mov', '.avi')):
            type_counts['Videos'] += count
        elif file_name.endswith(('.mp3', '.wav', '.aac')):
            type_counts['Audio'] += count
        else:
            type_counts['Others'] += count

    data = [{'file_type': k, 'count': v} for k, v in type_counts.items()]
    return JsonResponse(data, safe=False)


# View for storage usage over time
def storage_usage_over_time(request):
    storage_quota = 100 * 1024 * 1024  # 100 MB in bytes

    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    data = (
        File.objects.filter(created_at__range=[start_date, end_date], trashed=False, user=request.user)
        .extra({'day': "date(created_at)"})
        .values('day')
        .annotate(total_size=Sum('size'))
        .order_by('day')
    )

    cumulative_usage = 0
    usage_data = []
    for entry in data:
        cumulative_usage += entry['total_size']
        usage_data.append({
            'day': entry['day'],
            'cumulative_size': cumulative_usage
        })

    return JsonResponse({
        'usage_data': usage_data,
        'storage_quota': storage_quota
    }, safe=False)


@login_required
def ai_insight(request):
    """
    GET /dashboard/ai-insight/
    Returns a cached or freshly-generated Claude storage insight for the current user.
    Accepts ?refresh=1 to force regeneration.
    """
    force = request.GET.get("refresh", "0") == "1"
    result = generate_storage_insight(request.user, force_refresh=force)
    return JsonResponse({
        "insight": result["insight"],
        "generated_at": result["generated_at"],
        "stats": result["stats"],
        "from_cache": result["from_cache"],
    })
