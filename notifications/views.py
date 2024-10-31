from django.shortcuts import render, redirect
from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('notification_list')
