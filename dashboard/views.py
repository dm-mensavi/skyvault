from django.http import JsonResponse
from django.shortcuts import render
from vault.models import File
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

# Render the dashboard page
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')

# View for file type distribution
def file_type_distribution(request):
    # Calculate counts for each file type based on the extension or file categories
    file_type_counts = (
        File.objects.filter(trashed=False, user=request.user)  # Filter by the current user
        .values('uploaded_file')
        .annotate(count=Count('id'))
    )
    
    # Categorize file types into "Documents", "Images", etc., based on file extensions
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

    # Prepare data for JSON response
    data = [{'file_type': k, 'count': v} for k, v in type_counts.items()]
    return JsonResponse(data, safe=False)


# View for storage usage over time
def storage_usage_over_time(request):
    # Define storage quota in bytes (100 MB)
    storage_quota = 100 * 1024 * 1024  # 100 MB in bytes

    # Calculate cumulative storage usage grouped by day over the last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    data = (
        File.objects.filter(created_at__range=[start_date, end_date], trashed=False, user=request.user)  # Filter by the current user
        .extra({'day': "date(created_at)"})
        .values('day')
        .annotate(total_size=Sum('size'))
        .order_by('day')
    )

    # Calculate cumulative usage
    cumulative_usage = 0
    usage_data = []
    for entry in data:
        cumulative_usage += entry['total_size']  # Accumulate storage usage over time
        usage_data.append({
            'day': entry['day'],
            'cumulative_size': cumulative_usage
        })

    # Return storage usage data and storage quota
    return JsonResponse({
        'usage_data': usage_data,
        'storage_quota': storage_quota
    }, safe=False)
