from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

# Sign-up View
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')  # Redirect to login after signup
        else:
            messages.error(request, 'Sign up failed. Please check the form.')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

# Login View
def login_view(request):
  if request.method == 'POST':
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(username=username, password=password)
      if user is not None:
        login(request, user)
        messages.success(request, 'You have been logged in successfully.')
        return redirect('home')  # Redirect to home page after login
      else:
        messages.error(request, 'Invalid username or password.')
    else:
      messages.error(request, 'Invalid login credentials.')
  
  form = AuthenticationForm()
  return render(request, 'accounts/login.html', {'form': form})

# Logout View
def logout_view(request):
  logout(request)
  messages.success(request, 'You have been logged out successfully.')
  return redirect('login')


