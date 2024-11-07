from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import File, Folder
from .forms import *
from django.http import JsonResponse
from django.core.files.base import ContentFile
import json


# views.py
@login_required
def delete_file(request, file_id):
    if request.method == 'POST':
        file_instance = get_object_or_404(File, id=file_id, user=request.user)
        # Move the file to trash
        file_instance.trashed = True
        file_instance.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

@login_required
def delete_folder(request, folder_id):
    if request.method == 'POST':
        folder_instance = get_object_or_404(Folder, id=folder_id, user=request.user)
        # Cascade move to trash
        def move_folder_to_trash(folder):
            folder.trashed = True
            folder.save()
            # Move all files in this folder to trash
            files = folder.files.all()
            for file in files:
                file.trashed = True
                file.save()
            # Recursively move subfolders to trash
            subfolders = folder.subfolders.all()
            for subfolder in subfolders:
                move_folder_to_trash(subfolder)

        move_folder_to_trash(folder_instance)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)



# Restore a file or folder
@login_required
def restore_item(request, item_type, item_id):
    if request.method == 'POST':
        if item_type == 'folder':
            item = get_object_or_404(Folder, id=item_id, user=request.user, trashed=True)
        elif item_type == 'file':
            item = get_object_or_404(File, id=item_id, user=request.user, trashed=True)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid item type'}, status=400)

        # Restore the item by marking it as not trashed
        item.trashed = False
        item.save()
        return JsonResponse({'success': True, 'message': f'{item_type.capitalize()} restored successfully.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def delete_permanent_item(request, item_type, item_id):
    if request.method == 'POST':
        if item_type == 'folder':
            item = get_object_or_404(Folder, id=item_id, user=request.user, trashed=True)
        elif item_type == 'file':
            item = get_object_or_404(File, id=item_id, user=request.user, trashed=True)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid item type'}, status=400)

        item.delete()  # Permanently delete the item
        return JsonResponse({'success': True, 'message': f'{item_type.capitalize()} permanently deleted.'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def upload_file(request):
    if request.method != "POST":
        return redirect('vault_home')

    uploaded_file = request.FILES.get('uploaded_file')
    if not uploaded_file:
        messages.error(request, "No file selected.")
        return redirect('vault_home')

    folder_id = request.POST.get('folder_id')
    folder = None

    # Retrieve the folder if folder_id is provided
    if folder_id:
        folder = get_object_or_404(Folder, id=folder_id, user=request.user)

    user_profile = request.user.userprofile

    # Check for file size limits
    if uploaded_file.size > 40 * 1024 * 1024:  # 40 MB limit
        messages.error(request, "File exceeds max size of 40 MB.")
        return redirect('vault_home')

    # Check if user has exceeded storage limits
    if user_profile.is_storage_exceeded(uploaded_file.size):
        messages.error(request, "Storage limit exceeded.")
        return redirect('vault_home')

    # Check if a file with the same name already exists in the selected folder
    if File.objects.filter(user=request.user, name=uploaded_file.name, folder=folder).exists():
        messages.error(request, "File already exists in the selected folder.")
        return redirect('view_folder', folder_id=folder.id) if folder else redirect('vault_home')

    # Save the file and update user's used storage space
    File.objects.create(
        user=request.user,
        folder=folder,  # Assign to the selected folder or None for root level
        name=uploaded_file.name,
        uploaded_file=uploaded_file,
        size=uploaded_file.size,
    )
    user_profile.used_space += uploaded_file.size
    user_profile.save()

    messages.success(request, "File uploaded successfully!")
    return redirect('view_folder', folder_id=folder.id) if folder else redirect('vault_home')


@login_required
def create_folder(request):
    if request.method != "POST":
        return redirect('vault_home')

    folder_name = request.POST.get('folder_name')
    parent_folder_id = request.POST.get('parent_folder_id')

    # Retrieve the parent folder if provided
    parent_folder = None
    if parent_folder_id:
        parent_folder = get_object_or_404(Folder, id=parent_folder_id, user=request.user)

    # Check if folder name is provided
    if not folder_name:
        messages.error(request, "Folder name cannot be empty.")
        return redirect('view_folder', folder_id=parent_folder_id) if parent_folder else redirect('vault_home')

    # Check for duplicate folder names within the same parent folder
    if Folder.objects.filter(user=request.user, name=folder_name, parent_folder=parent_folder).exists():
        messages.error(request, "Folder name already exists. Please choose a different name.")
        return redirect('view_folder', folder_id=parent_folder_id) if parent_folder else redirect('vault_home')

    # Create and save the folder
    Folder.objects.create(user=request.user, name=folder_name, parent_folder=parent_folder)
    messages.success(request, "Folder created successfully!")

    # Redirect to the appropriate view
    return redirect('view_folder', folder_id=parent_folder.id) if parent_folder else redirect('vault_home')


@login_required
def view_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user, trashed=False)
    subfolders = folder.subfolders.filter(trashed=False)
    files = folder.files.filter(trashed=False)         # Retrieve files within this folder

    return render(request, 'vault/view_folder.html', {
        'folder': folder,
        'subfolders': subfolders,
        'files': files,
    })

@login_required
def open_file(request, file_id):
    file_instance = get_object_or_404(File, id=file_id, user=request.user)

    # Determine file type from extension
    file_extension = file_instance.uploaded_file.name.split('.')[-1].lower()
    
    # If the file is an image or text, try displaying it directly
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        return FileResponse(file_instance.uploaded_file.open(), content_type=f'image/{file_extension}')
    
    elif file_extension in ['txt', 'pdf']:
        return FileResponse(file_instance.uploaded_file.open(), content_type='application/pdf' if file_extension == 'pdf' else 'text/plain')

    # For other file types, prompt download
    response = FileResponse(file_instance.uploaded_file.open(), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{file_instance.name}"'
    return response


@login_required
def paste(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")
        item_type = data.get("item_type")
        action = data.get("action")
        target_folder_id = data.get("target_folder")

        print("Paste action data received:", data)  # Debug print

        # Get the target folder
        if target_folder_id:
            target_folder = get_object_or_404(Folder, id=target_folder_id, user=request.user)
        else:
            target_folder = None  # Root folder

        if item_type == "file":
            item = get_object_or_404(File, id=item_id, user=request.user)
            if action == "copy":
                # Open the uploaded file and read its content
                item.uploaded_file.open()
                file_content = item.uploaded_file.read()
                item.uploaded_file.close()

                # Create a new file instance
                new_file = File.objects.create(
                    user=request.user,
                    name=item.name,
                    folder=target_folder,
                    size=item.size,
                    trashed=item.trashed,
                    starred=item.starred,
                    # Copy other necessary fields
                )
                new_file.uploaded_file.save(item.uploaded_file.name, ContentFile(file_content))
                new_file.save()
                message = "File copied successfully!"
                print(message)  # Debug print

            elif action == "cut":
                # Move the file to the target folder
                print(f"Before moving: File {item.id} in folder {item.folder_id}")
                item.folder = target_folder
                item.save()
                print(f"After moving: File {item.id} in folder {item.folder_id}")
                message = "File moved successfully!"
                print(message)  # Debug print

            else:
                return JsonResponse({"success": False, "message": "Invalid action"}, status=400)

        elif item_type == "folder":
            item = get_object_or_404(Folder, id=item_id, user=request.user)
            if action == "copy":
                # Recursive function to copy folders and their contents
                def copy_folder(folder_to_copy, parent_folder):
                    new_folder = Folder.objects.create(
                        user=request.user,
                        name=folder_to_copy.name + " (Copy)",
                        parent_folder=parent_folder
                    )
                    # Copy files in this folder
                    files = File.objects.filter(folder=folder_to_copy)
                    for file in files:
                        file.uploaded_file.open()
                        file_content = file.uploaded_file.read()
                        file.uploaded_file.close()

                        new_file = File.objects.create(
                            user=request.user,
                            name=file.name,
                            folder=new_folder,
                            size=file.size,
                            trashed=file.trashed,
                            starred=file.starred,
                            # Copy other necessary fields
                        )
                        new_file.uploaded_file.save(file.uploaded_file.name, ContentFile(file_content))
                        new_file.save()
                    # Recursively copy subfolders
                    subfolders = Folder.objects.filter(parent_folder=folder_to_copy)
                    for subfolder in subfolders:
                        copy_folder(subfolder, new_folder)
                    return new_folder

                copy_folder(item, target_folder)
                message = "Folder copied successfully!"
                print(message)  # Debug print

            elif action == "cut":
                # Move the folder to the target location
                item.parent_folder = target_folder
                item.save()
                message = "Folder moved successfully!"
                print(message)  # Debug print

            else:
                return JsonResponse({"success": False, "message": "Invalid action"}, status=400)

        else:
            return JsonResponse({"success": False, "message": "Invalid item type"}, status=400)

        return JsonResponse({"success": True, "message": message})
    else:
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)


@login_required
def vault_home(request):
    folders = Folder.objects.filter(user=request.user, parent_folder__isnull=True, trashed=False)
    files = File.objects.filter(user=request.user, folder__isnull=True, trashed=False)
    
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

    return render(request, 'vault/vault.html', {
        'folders': folders,
        'files': files,
        'folder_form': folder_form,
        'file_form': file_form,
    })

    
@login_required
def trash_view(request):
    trashed_folders = Folder.objects.filter(user=request.user, trashed=True)
    trashed_files = File.objects.filter(user=request.user, trashed=True)
    return render(request, 'vault/trash.html', {
        'trashed_folders': trashed_folders,
        'trashed_files': trashed_files,
    })

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

@login_required
def toggle_star(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")
        item_type = data.get("item_type")

        # Retrieve the file or folder based on the item type
        if item_type == "file":
            item = get_object_or_404(File, id=item_id, user=request.user)
        elif item_type == "folder":
            item = get_object_or_404(Folder, id=item_id, user=request.user)
        else:
            return JsonResponse({"success": False, "message": "Invalid item type"}, status=400)

        # Print current status before changing
        print(f"Current starred status for {item_type} {item_id}: {item.starred}")

        # Toggle the starred status
        item.starred = not item.starred
        item.save()

        # Print new status to confirm change
        print(f"New starred status for {item_type} {item_id}: {item.starred}")

        status = "starred" if item.starred else "unstarred"
        return JsonResponse({"success": True, "message": f"{item_type.capitalize()} successfully {status}."})

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)

