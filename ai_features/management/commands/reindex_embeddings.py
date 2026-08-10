from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User

from ai_features.models import FileAnalysis
from ai_features.services.embeddings import embed_text
from ai_features.tasks import _index_vector_chunks


class Command(BaseCommand):
    help = (
        "Rebuilds pgvector DocumentChunk rows from already-extracted text. "
        "Needed after migration 0006 cleared all chunks, since analyze_file only "
        "runs on upload. Re-uses stored extracted_text, so no re-extraction and "
        "no Claude calls are made."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            dest="username",
            default=None,
            help="Only reindex files belonging to this username.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reindex files that already have chunks (default: skip them).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SkyVault Vector Reindex ==="))

        # Fail loudly up front: without a working embedding model this command
        # would "succeed" while writing nothing at all.
        model_name = getattr(settings, "AI_EMBEDDING_MODEL", "")
        self.stdout.write(f"Embedding model: {model_name}")
        probe = embed_text("SkyVault embedding availability probe")
        expected_dims = getattr(settings, "AI_EMBEDDING_DIMENSIONS", 384)
        if not probe:
            raise CommandError(
                "Embedding model unavailable — embed_text() returned an empty vector. "
                f"Check that sentence-transformers is installed and that "
                f"AI_EMBEDDING_MODEL ('{model_name}') is a valid HuggingFace model id. "
                "Run 'python manage.py ai_smoke_test' for details. Nothing was reindexed."
            )
        if len(probe) != expected_dims:
            raise CommandError(
                f"Embedding dimension mismatch: model produced {len(probe)} dims, "
                f"but the DocumentChunk column expects {expected_dims}. "
                "Nothing was reindexed."
            )
        self.stdout.write(self.style.SUCCESS(f"   [OK] Embeddings live ({len(probe)} dims)."))

        analyses = (
            FileAnalysis.objects.exclude(extracted_text="")
            .select_related("file")
            .order_by("file_id")
        )

        username = options["username"]
        if username:
            if not User.objects.filter(username=username).exists():
                raise CommandError(f"No user named '{username}'.")
            analyses = analyses.filter(file__user__username=username)
            self.stdout.write(f"Scoped to user: {username}")

        analyses = analyses.filter(file__trashed=False)

        total = analyses.count()
        if not total:
            self.stdout.write(
                self.style.WARNING(
                    "No analyses with stored extracted_text found. Nothing to reindex. "
                    "Re-upload files, or check that analyze_file has run."
                )
            )
            return

        self.stdout.write(f"\nFound {total} file(s) with extracted text.\n")

        indexed = skipped = failed = 0

        for analysis in analyses.iterator():
            file_obj = analysis.file
            existing = file_obj.chunks.count()

            if existing and not options["force"]:
                self.stdout.write(f"  - {file_obj.name}: {existing} chunk(s) already, skipping.")
                skipped += 1
                continue

            try:
                _index_vector_chunks(file_obj, analysis, analysis.extracted_text)
            except Exception as e:
                # _index_vector_chunks swallows its own errors, but guard anyway
                # so one bad file cannot abort the whole run.
                self.stdout.write(self.style.ERROR(f"  x {file_obj.name}: {e}"))
                failed += 1
                continue

            new_count = file_obj.chunks.count()
            if new_count:
                self.stdout.write(self.style.SUCCESS(f"  + {file_obj.name}: {new_count} chunk(s)."))
                indexed += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ! {file_obj.name}: produced no chunks (see logs).")
                )
                failed += 1

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n=== Reindex complete: {indexed} indexed, {skipped} skipped, {failed} failed ==="
            )
        )
        if skipped and not options["force"]:
            self.stdout.write("Use --force to rebuild files that already have chunks.")
