import os
import tempfile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from vault.models import File, Folder


DEMO_FILES = [
    {
        "name": "tax_return_2024.pdf",
        "content": (
            b"Tax Return 2024\n\n"
            b"This document contains my 2024 tax return with income details, "
            b"deductions, and credits. Filed with the IRS on April 15, 2025. "
            b"Total refund expected: $1,240."
        ),
    },
    {
        "name": "invoice_billing_jan.pdf",
        "content": (
            b"Invoice #INV-2024-001\n\n"
            b"Bill Amount: $3,450.00\n"
            b"Client: Acme Corp\n"
            b"Services rendered: consulting\n"
            b"Payment due: January 31, 2025\n"
            b"Status: PAID"
        ),
    },
    {
        "name": "invoice_quarterly_q2.pdf",
        "content": (
            b"Invoice #INV-2024-Q2\n\n"
            b"Bill Amount: $7,800.00\n"
            b"Client: Globex Industries\n"
            b"Services: development sprint\n"
            b"Payment due: July 15, 2024\n"
            b"Status: PAID"
        ),
    },
    {
        "name": "resume_curriculum_vitae.pdf",
        "content": (
            b"John Smith - Software Engineer Resume\n\n"
            b"Experience: 5 years at Galleon Tech\n"
            b"Skills: Python, Django, PostgreSQL, React\n"
            b"Education: MIT Computer Science 2018"
        ),
    },
    {
        "name": "cover_letter_job_application.pdf",
        "content": (
            b"Cover Letter for Senior Developer Position\n\n"
            b"Dear Hiring Manager,\n\n"
            b"I am writing to apply for the Senior Developer role at "
            b"Decathlon Industries. My experience aligns with your needs."
        ),
    },
    {
        "name": "meeting_notes_calendar.pdf",
        "content": (
            b"Meeting Notes - Academic Year Planning\n\n"
            b"Date: September 1, 2024\n"
            b"Attendees: faculty council\n"
            b"Topics: semester schedule, exam dates, room bookings\n"
            b"Action items: finalize timetable by Sept 15"
        ),
    },
    {
        "name": "code_review_final.pdf",
        "content": (
            b"Code Review - Interactive Engineering\n\n"
            b"Review of the new API endpoint for user authentication.\n"
            b"Comments:\n"
            b"1. Add rate limiting on the login endpoint\n"
            b"2. Use parameterized queries to prevent SQL injection\n"
            b"3. Add integration tests for the token refresh flow"
        ),
    },
    {
        "name": "project_milestones.pdf",
        "content": (
            b"Project Milestones Q3 2024\n\n"
            b"1. Backend API complete - August 1\n"
            b"2. Frontend redesign - August 15\n"
            b"3. QA testing - September 1\n"
            b"4. Production deploy - September 15\n"
            b"5. Post-launch review - September 30"
        ),
    },
    {
        "name": "budget_forecast_2025.pdf",
        "content": (
            b"Budget Forecast 2025\n\n"
            b"Q1: $50,000 projected spend\n"
            b"Q2: $45,000 projected spend\n"
            b"Q3: $60,000 projected spend\n"
            b"Q4: $55,000 projected spend\n"
            b"Total annual budget: $210,000"
        ),
    },
    {
        "name": "readme_project_guidelines.pdf",
        "content": (
            b"Project Guidelines\n\n"
            b"This repository contains the SkyVault file management system.\n"
            b"Contributing guidelines:\n"
            b"1. Fork the repository\n"
            b"2. Create a feature branch\n"
            b"3. Write tests for new features\n"
            b"4. Submit a pull request"
        ),
    },
    {
        "name": "contract_2024.pdf",
        "content": (
            b"Client Contract 2024\n\n"
            b"Party A: SkyVault Inc.\n"
            b"Party B: Acme Corp\n"
            b"Services: File management platform\n"
            b"Term: 12 months starting January 1, 2024\n"
            b"Value: $120,000"
        ),
    },
    {
        "name": "travel_receipts_2024.pdf",
        "content": (
            b"Travel Receipts 2024\n\n"
            b"Jan 15 - Flight to NYC - $340\n"
            b"Feb 3 - Hotel Boston - $180\n"
            b"Mar 22 - Meals - $75\n"
            b"Apr 10 - Flight to Chicago - $280\n"
            b"Total: $875"
        ),
    },
]


class Command(BaseCommand):
    help = "Creates a demo user with sample files for AI feature evaluation and demos."

    def handle(self, *args, **options):
        username = "demouser"
        password = "demopass123"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Created demo user: {username}"
            ))
        else:
            self.stdout.write(
                f"User '{username}' already exists. Skipping creation."
            )

        root_folder, _ = Folder.objects.get_or_create(
            user=user, name="Demo Vault", parent_folder=None,
        )

        for demo_file in DEMO_FILES:
            File.objects.filter(user=user, name=demo_file["name"]).delete()

            file_obj = File(
                user=user,
                folder=root_folder,
                name=demo_file["name"],
                size=len(demo_file["content"]),
            )
            file_obj.uploaded_file.save(
                demo_file["name"],
                ContentFile(demo_file["content"]),
            )
            file_obj.save()

            self.stdout.write(f"  Created file: {demo_file['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Demo user '{username}' with "
            f"{len(DEMO_FILES)} sample files ready."
        ))
        self.stdout.write(self.style.NOTICE(
            "Files are in folder 'Demo Vault'. "
            "Run `python manage.py run_search_eval` to benchmark retrieval "
            "after Phase 2 indexing is complete."
        ))