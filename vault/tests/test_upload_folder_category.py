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
        self.assertEqual(classify_system_category("invoice_2024.pdf", "pdf"), "Invoices")
        self.assertEqual(classify_system_category("Dossier_de_candidature.pdf", "pdf"), "Digital Campus")
        self.assertEqual(classify_system_category("script.py", "py"), "Code & Scripts")
        self.assertEqual(classify_system_category("data.csv", "csv"), "Data & Spreadsheets")
        self.assertEqual(classify_system_category("photo.png", "png"), "Images & Media")
        self.assertEqual(classify_system_category("my_resume.docx", "docx"), "Resumes")
        self.assertEqual(classify_system_category("random_notes.txt", "txt"), "Documents")

    def test_single_file_upload_creates_suggested_folder(self):
        uploaded_file = SimpleUploadedFile("Tax_Return_2024.pdf", b"tax declaration text", content_type="application/pdf")

        response = self.client.post(
            reverse("upload_file"),
            {"uploaded_file": uploaded_file},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_single"])
        self.assertEqual(data["category"], "Taxes")
        self.assertEqual(data["folder_name"], "Taxes")
        self.assertEqual(data["file_name"], "Tax_Return_2024.pdf")

        # Verify folder and file were created in DB with suggested folder name
        folder = Folder.objects.get(id=data["folder_id"])
        file_obj = File.objects.get(id=data["file_id"])

        self.assertEqual(folder.name, "Taxes")
        self.assertEqual(folder.category, "Taxes")
        self.assertEqual(file_obj.folder, folder)
        self.assertEqual(file_obj.category, "Taxes")

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

    def test_auto_organize_file_to_suggested_folder(self):
        from vault.views import auto_organize_file_to_suggested_folder

        # Create a file in a generic folder
        folder = Folder.objects.create(user=self.user, name="General", category="General")
        file_obj = File.objects.create(
            user=self.user,
            folder=folder,
            name="Dossier_de_candidature.pdf",
            size=1024,
            category="General"
        )

        # Auto organize to AI's suggested folder "Digital Campus"
        new_folder = auto_organize_file_to_suggested_folder(file_obj, "Digital Campus")

        self.assertIsNotNone(new_folder)
        self.assertEqual(new_folder.name, "Digital Campus")

        # Refetched file should now belong to Digital Campus folder
        file_obj.refresh_from_db()
        self.assertEqual(file_obj.folder, new_folder)
        self.assertEqual(file_obj.category, "Digital Campus")

        # Old generic folder should have been cleaned up since it became empty
        self.assertFalse(Folder.objects.filter(id=folder.id).exists())
