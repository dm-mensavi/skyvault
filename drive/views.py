from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserProfileForm
from .models import UserProfile

@login_required
def profile_view(request):
  user_profile, created = UserProfile.objects.get_or_create(user=request.user)  # Ensure this fetches or creates the profile

  return render(request, 'profile.html', {'user_profile': user_profile})

@login_required
def profile_update_view(request):
  user_profile, created = UserProfile.objects.get_or_create(user=request.user)
  if request.method == 'POST':
    form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
    if form.is_valid():
      form.save()
      messages.success(request, "Profile updated successfully.")
      return redirect('profile')
  else:
    form = UserProfileForm(instance=user_profile)

  return render(request, 'profile_update.html', {'form': form})
