from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from ai_features.services.claude import generate_json, get_anthropic_client, _generate_text_fallback
from ai_features.services.embeddings import embed_text, get_openai_client


class Command(BaseCommand):
    help = "Diagnostic smoke test for SkyVault AI infrastructure (PostgreSQL pgvector, generation endpoints, embeddings)."

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

        # 2. Test primary generation endpoint (Anthropic-compatible)
        self.stdout.write("\n2. Testing primary generation endpoint (Anthropic-compatible)...")
        anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        base_url = getattr(settings, "ANTHROPIC_BASE_URL", "") or "https://api.anthropic.com (default)"
        model = getattr(settings, "AI_CLAUDE_MODEL", "")
        if not anthropic_key:
            self.stdout.write(self.style.WARNING("   [NOTICE] ANTHROPIC_AUTH_TOKEN/ANTHROPIC_API_KEY is missing/empty. Skipping live API call."))
        else:
            self.stdout.write(self.style.SUCCESS(f"   [OK] Auth token configured ({anthropic_key[:6]}...)."))
            self.stdout.write(f"   Endpoint: {base_url} | Model: {model}")
            client = get_anthropic_client()
            if client:
                self.stdout.write("   Calling generation API for test JSON response...")
                result = generate_json(
                    system_prompt="You are a classifier test assistant.",
                    user_content="Categorize document: 'SkyVault Project Specification 2026'",
                    schema_description='{"tags": list[str], "category": str}'
                )
                if result:
                    self.stdout.write(self.style.SUCCESS(f"   [SUCCESS] JSON Response: {result}"))
                else:
                    self.stdout.write(self.style.ERROR("   [FAIL] Generation returned empty or invalid response."))

        # 3. Test fallback generation model
        self.stdout.write("\n3. Testing fallback generation model...")
        fallback_model = getattr(settings, "AI_FALLBACK_MODEL", "")
        if not fallback_model:
            self.stdout.write(self.style.WARNING("   [NOTICE] AI_FALLBACK_MODEL not set. Fallback disabled."))
        else:
            fb_base = getattr(settings, "AI_FALLBACK_BASE_URL", "") or "https://api.anthropic.com (default)"
            self.stdout.write(f"   Endpoint: {fb_base} | Model: {fallback_model}")
            text = _generate_text_fallback("You are a test assistant.", "Reply with the single word: OK", max_tokens=20)
            if text:
                self.stdout.write(self.style.SUCCESS(f"   [SUCCESS] Fallback response: {text.strip()[:80]}"))
            else:
                self.stdout.write(self.style.ERROR("   [FAIL] Fallback model returned no text."))

        # 4. Test embeddings integration (OpenAI-compatible)
        self.stdout.write("\n4. Testing Embeddings API Integration (OpenAI-compatible)...")
        openai_key = getattr(settings, "OPENAI_API_KEY", "")
        openai_base = getattr(settings, "OPENAI_BASE_URL", "") or "https://api.openai.com/v1 (default)"
        if not openai_key:
            self.stdout.write(self.style.WARNING("   [NOTICE] OPENAI_API_KEY is missing/empty. Skipping live API call."))
        else:
            self.stdout.write(self.style.SUCCESS(f"   [OK] OPENAI_API_KEY configured ({openai_key[:6]}...)."))
            self.stdout.write(f"   Endpoint: {openai_base} | Model: {getattr(settings, 'AI_EMBEDDING_MODEL', '')}")
            client = get_openai_client()
            if client:
                self.stdout.write("   Generating test embedding vector (1536 dims)...")
                vec = embed_text("SkyVault cloud file management system")
                if vec and len(vec) == 1536:
                    self.stdout.write(self.style.SUCCESS(f"   [SUCCESS] Received 1536-dim embedding vector! Sample: {vec[:3]}..."))
                else:
                    self.stdout.write(self.style.ERROR(f"   [FAIL] Vector generation unexpected result: len={len(vec) if vec else 0}"))

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Smoke Test Complete ==="))
