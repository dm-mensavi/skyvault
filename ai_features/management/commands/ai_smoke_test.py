from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from ai_features.services.claude import generate_json, get_anthropic_client
from ai_features.services.embeddings import embed_text, get_openai_client


class Command(BaseCommand):
    help = "Diagnostic smoke test for SkyVault AI infrastructure (PostgreSQL pgvector, Claude API, OpenAI Embeddings)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SkyVault AI Infrastructure Smoke Test ==="))

        # 1. Test PostgreSQL pgvector extension
        self.stdout.write("\n1. Testing PostgreSQL pgvector extension...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                row = cursor.fetchone()
                if row:
                    self.stdout.write(self.style.SUCCESS("   [OK] PostgreSQL pgvector extension is ACTIVE in database."))
                else:
                    self.stdout.write(self.style.ERROR("   [FAIL] pgvector extension NOT found in database."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   [FAIL] Database check failed: {e}"))

        # 2. Test Anthropic Claude integration
        self.stdout.write("\n2. Testing Anthropic Claude API Integration...")
        anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if not anthropic_key:
            self.stdout.write(self.style.WARNING("   [NOTICE] ANTHROPIC_API_KEY is missing/empty. Skipping live API call."))
        else:
            self.stdout.write(self.style.SUCCESS(f"   [OK] ANTHROPIC_API_KEY configured ({anthropic_key[:6]}...)."))
            client = get_anthropic_client()
            if client:
                self.stdout.write("   Calling Claude API for test JSON response...")
                result = generate_json(
                    system_prompt="You are a classifier test assistant.",
                    user_content="Categorize document: 'SkyVault Project Specification 2026'",
                    schema_description='{"tags": list[str], "category": str}'
                )
                if result:
                    self.stdout.write(self.style.SUCCESS(f"   [SUCCESS] Claude JSON Response: {result}"))
                else:
                    self.stdout.write(self.style.ERROR("   [FAIL] Claude returned empty or invalid response."))

        # 3. Test OpenAI Embeddings integration
        self.stdout.write("\n3. Testing OpenAI Embeddings API Integration...")
        openai_key = getattr(settings, "OPENAI_API_KEY", "")
        if not openai_key:
            self.stdout.write(self.style.WARNING("   [NOTICE] OPENAI_API_KEY is missing/empty. Skipping live API call."))
        else:
            self.stdout.write(self.style.SUCCESS(f"   [OK] OPENAI_API_KEY configured ({openai_key[:6]}...)."))
            client = get_openai_client()
            if client:
                self.stdout.write("   Generating test embedding vector (1536 dims)...")
                vec = embed_text("SkyVault cloud file management system")
                if vec and len(vec) == 1536:
                    self.stdout.write(self.style.SUCCESS(f"   [SUCCESS] Received 1536-dim embedding vector! Sample: {vec[:3]}..."))
                else:
                    self.stdout.write(self.style.ERROR(f"   [FAIL] Vector generation unexpected result: len={len(vec) if vec else 0}"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Smoke Test Complete ==="))
