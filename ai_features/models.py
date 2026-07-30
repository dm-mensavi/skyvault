from django.db import models
from pgvector.django import VectorField, HnswIndex


class FileAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING     = "pending", "Pending"
        PROCESSING  = "processing", "Processing"
        DONE        = "done", "Done"
        FAILED      = "failed", "Failed"
        SKIPPED     = "skipped", "Skipped"

    file            = models.OneToOneField("vault.File", on_delete=models.CASCADE, related_name="analysis")
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    summary         = models.TextField(blank=True)
    tags            = models.JSONField(default=list)
    suggested_folder= models.CharField(max_length=255, blank=True)
    extracted_text  = models.TextField(blank=True)
    error_message   = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis ({self.status}) for {self.file.name}"


class DocumentChunk(models.Model):
    file        = models.ForeignKey("vault.File", on_delete=models.CASCADE, related_name="chunks")
    analysis    = models.ForeignKey(FileAnalysis, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content     = models.TextField()
    embedding   = VectorField(dimensions=1536)
    token_count = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("file", "chunk_index")
        ordering = ["file", "chunk_index"]
        indexes = [
            HnswIndex(
                name="docchunk_embedding_hnsw_idx",
                fields=["embedding"],
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self):
        return f"Chunk #{self.chunk_index} for {self.file.name}"


class StorageInsight(models.Model):
    """
    Caches a Claude-generated natural-language storage insight per user.
    Regenerated on demand (manual refresh) or can be scheduled daily.
    """
    user        = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="storage_insight")
    insight     = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)
    stats_snapshot = models.JSONField(default=dict)  # stores the aggregated stats used

    def __str__(self):
        return f"StorageInsight for {self.user.username} @ {self.generated_at}"

