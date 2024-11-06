from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import File, Folder
from .forms import *

@login_required
def upload_file(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('uploaded_file')
        if not uploaded_file:
            messages.error(request, "No file selected.")
            return redirect('vault_home')

        user_profile = request.user.userprofile

        # Check for file size limits
        if uploaded_file.size > 40 * 1024 * 1024:  # 40 MB limit
            messages.error(request, "File exceeds max size of 40 MB.")
            return redirect('vault_home')

        if user_profile.is_storage_exceeded(uploaded_file.size):
            messages.error(request, "Storage limit exceeded.")
            return redirect('vault_home')

        # Save the file and update used space
        File.objects.create(
            user=request.user,
            folder=None,
            name=uploaded_file.name,
            uploaded_file=uploaded_file,
            size=uploaded_file.size,
        )
        user_profile.used_space += uploaded_file.size
        user_profile.save()

        messages.success(request, "File uploaded successfully!")
        return redirect('vault_home')
    return redirect('vault_home')


@login_required
def create_folder(request):
    if request.method == "POST":
        folder_name = request.POST.get('folder_name')
        if not folder_name:
            messages.error(request, "Folder name cannot be empty.")
            return redirect('vault_home')

        Folder.objects.create(user=request.user, name=folder_name)
        messages.success(request, "Folder created successfully!")
        return redirect('vault_home')
    return redirect('vault_home')


@login_required
def vault_home(request):
    folders = Folder.objects.filter(user=request.user)
    files = File.objects.filter(user=request.user, trashed=False)

    if request.method == "POST":
        if 'folder_name' in request.POST:
            folder_form = FolderForm(request.POST)
            if folder_form.is_valid():
                new_folder = folder_form.save(commit=False)
                new_folder.user = request.user
                new_folder.save()
                messages.success(request, "Folder created successfully!")
                return redirect('vault_home')
            else:
                messages.error(request, "Error creating folder. Please try again.")
        
        elif 'uploaded_file' in request.FILES:
            file_form = FileUploadForm(request.POST, request.FILES)
            if file_form.is_valid():
                new_file = file_form.save(commit=False)
                new_file.user = request.user
                new_file.size = request.FILES['uploaded_file'].size
                new_file.save()
                messages.success(request, "File uploaded successfully!")
                return redirect('vault_home')
            else:
                messages.error(request, "Error uploading file. Please try again.")
    
    folder_form = FolderForm()
    file_form = FileUploadForm()

    return render(request, 'vault/home.html', {
        'folders': folders,
        'files': files,
        'folder_form': folder_form,
        'file_form': file_form,
    })

    
@login_required
def trash_view(request):
    trashed_files = File.objects.filter(user=request.user, trashed=True)
    return render(request, 'vault/trash.html', {'trashed_files': trashed_files})

@login_required
def shared_view(request):
    shared_files = request.user.shared_files.all()  # Files shared with the user
    return render(request, 'vault/shared.html', {'shared_files': shared_files})

@login_required
def search_view(request):
    query = request.GET.get('q', '')
    results = File.objects.filter(user=request.user, name__icontains=query, trashed=False) if query else []
    return render(request, 'vault/search.html', {'results': results, 'query': query})

@login_required
def recent_files(request):
    # Fetch recent files, ordering by date uploaded or modified
    recent_files = File.objects.filter(user=request.user).order_by('-id')[:10]  # Adjust limit as needed
    return render(request, 'vault/recent_files.html', {'files': recent_files})

@login_required
def starred_files(request):
    # Fetch starred files (assuming `starred` is a boolean field we add to File model)
    starred_files = File.objects.filter(user=request.user, starred=True)
    return render(request, 'vault/starred_files.html', {'files': starred_files})

@login_required
def storage_info(request):
    # Display storage usage details
    user_files = File.objects.filter(user=request.user)
    total_storage = sum(file.size for file in user_files) / (1024 * 1024)  # Convert bytes to MB
    max_storage = 100  # 100 MB limit

    context = {
        'total_storage': total_storage,
        'max_storage': max_storage,
        'used_percentage': (total_storage / max_storage) * 100 if max_storage else 0,
    }
    return render(request, 'vault/storage_info.html', context)