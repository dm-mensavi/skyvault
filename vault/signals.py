from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from .models import File
from ai_features.models import FileAnalysis

TEXT_ALLOWLIST = {
    "pdf", "txt", "md", "docx", "doc", "json", "py", "js", "html", "css", "csv", "xml"
}


@receiver(post_save, sender=File)
def on_file_uploaded(sender, instance, created, **kwargs):
    if created and not instance.trashed:
        ext = instance.uploaded_file.name.split('.')[-1].lower() if instance.uploaded_file else ''

        if ext in TEXT_ALLOWLIST:
            FileAnalysis.objects.get_or_create(
                file=instance,
                defaults={"status": FileAnalysis.Status.PENDING}
            )
            async_task("ai_features.tasks.analyze_file", instance.id)
        else:
            FileAnalysis.objects.get_or_create(
                file=instance,
                defaults={"status": FileAnalysis.Status.SKIPPED}
            )
