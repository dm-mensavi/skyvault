import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from vault.models import Folder, File
from vault.views import classify_system_category
from settings.models import UserProfile


class UploadFolderCategoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.client.login(username="testuser", password="password123")

    def test_classify_system_category(self):
        self.assertEqual(classify_system_category("invoice_2024.pdf", "pdf"), "Financial")
        self.assertEqual(classify_system_category("script.py", "py"), "Code & Scripts")
        self.assertEqual(classify_system_category("data.csv", "csv"), "Data & Spreadsheets")
        self.assertEqual(classify_system_category("photo.png", "png"), "Images & Media")
        self.assertEqual(classify_system_category("my_resume.docx", "docx"), "Work")
        self.assertEqual(classify_system_category("random_notes.txt", "txt"), "Documents")

    def test_single_file_upload_creates_folder_and_returns_modal_data(self):
        uploaded_file = SimpleUploadedFile("Tax_Return_2024.pdf", b"pdf content", content_type="application/pdf")
        
        response = self.client.post(
            reverse("upload_file"),
            {"uploaded_file": uploaded_file},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_single"])
        self.assertEqual(data["category"], "Financial")
        self.assertEqual(data["folder_name"], "Tax_Return_2024")
        self.assertEqual(data["file_name"], "Tax_Return_2024.pdf")

        # Verify folder and file were created in DB
        folder = Folder.objects.get(id=data["folder_id"])
        file_obj = File.objects.get(id=data["file_id"])

        self.assertEqual(folder.name, "Tax_Return_2024")
        self.assertEqual(folder.category, "Financial")
        self.assertEqual(file_obj.folder, folder)
        self.assertEqual(file_obj.category, "Financial")

    def test_multi_file_upload_auto_categorizes(self):
        f1 = SimpleUploadedFile("app_code.py", b"print('hello')", content_type="text/plain")
        f2 = SimpleUploadedFile("budget_sheet.csv", b"a,b,c", content_type="text/csv")

        response = self.client.post(
            reverse("upload_file"),
            {"uploaded_file": [f1, f2]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_single"])
        self.assertEqual(data["count"], 2)

        # Check DB records created
        code_file = File.objects.get(name="app_code.py")
        sheet_file = File.objects.get(name="budget_sheet.csv")

        self.assertEqual(code_file.category, "Code & Scripts")
        self.assertEqual(code_file.folder.category, "Code & Scripts")

        self.assertEqual(sheet_file.category, "Data & Spreadsheets")
        self.assertEqual(sheet_file.folder.category, "Data & Spreadsheets")

    def test_confirm_upload_details_updates_name_and_category(self):
        uploaded_file = SimpleUploadedFile("raw_notes.txt", b"notes text", content_type="text/plain")
        res_upload = self.client.post(
            reverse("upload_file"),
            {"uploaded_file": uploaded_file},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        data_upload = res_upload.json()

        # Call confirm_upload_details endpoint to customize folder name, file name, category
        res_confirm = self.client.post(
            reverse("confirm_upload_details"),
            json.dumps({
                "folder_id": data_upload["folder_id"],
                "file_id": data_upload["file_id"],
                "folder_name": "Project Documentation",
                "file_name": "Final_Notes.txt",
                "category": "Work"
            }),
            content_type="application/json"
        )

        self.assertEqual(res_confirm.status_code, 200)
        data_confirm = res_confirm.json()
        self.assertTrue(data_confirm["success"])

        # Verify DB updates
        folder = Folder.objects.get(id=data_upload["folder_id"])
        file_obj = File.objects.get(id=data_upload["file_id"])

        self.assertEqual(folder.name, "Project Documentation")
        self.assertEqual(folder.category, "Work")
        self.assertEqual(file_obj.name, "Final_Notes.txt")
        self.assertEqual(file_obj.category, "Work")
