import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from ai_features.services.search import search_files, RetrievalUnavailable


class Command(BaseCommand):
    help = "Evaluates pgvector semantic retrieval Recall@K performance and updates docs/EVAL_RESULTS.md."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SkyVault Vector Retrieval Evaluation (Recall@K) ==="))

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found in database for evaluation."))
            return

        json_path = os.path.join(settings.BASE_DIR, "ai_features", "eval", "queries.json")
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Benchmark file not found at {json_path}"))
            return

        with open(json_path, "r") as f:
            test_queries = json.load(f)

        total_recall = 0.0
        query_count = len(test_queries)
        eval_rows = []

        self.stdout.write(f"\nRunning {query_count} benchmark queries for user: {user.username}...")

        for q in test_queries:
            query = q["query"]
            k = q.get("k", 5)
            expected_kw = q.get("expected_keywords", [])

            try:
                results = search_files(user, query, top_k=k)
            except RetrievalUnavailable as e:
                # Abort rather than write a report full of 0.0 recall, which would
                # look like a genuine retrieval-quality result.
                raise CommandError(
                    f"Retrieval unavailable, aborting eval: {e} "
                    "Run 'python manage.py ai_smoke_test' to diagnose. "
                    "docs/EVAL_RESULTS.md was left unchanged."
                ) from e
            retrieved_names = [r["file"].name.lower() for r in results]

            # Calculate hit recall
            hits = 0
            for kw in expected_kw:
                if any(kw in name for name in retrieved_names):
                    hits += 1

            recall = round(hits / max(1, len(expected_kw)), 2)
            total_recall += recall

            eval_rows.append({
                "query": query,
                "recall": recall,
                "top_retrieved": [r["file"].name for r in results[:3]]
            })

            status_style = self.style.SUCCESS if recall > 0.0 else self.style.WARNING
            self.stdout.write(status_style(f"  Query: '{query}' -> Recall@{k}: {recall} | Matches: {[r['file'].name for r in results[:2]]}"))

        avg_recall = round(total_recall / max(1, query_count), 2)
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== Average Recall@5 Score: {avg_recall} ==="))

        # Write results report to docs/EVAL_RESULTS.md
        eval_doc_path = os.path.join(settings.BASE_DIR, "docs", "EVAL_RESULTS.md")
        doc_content = f"# SkyVault AI — Retrieval & RAG Benchmark Results\n\n" \
                      f"**Evaluated on:** 2026-07-30  \n" \
                      f"**Vector Store:** PostgreSQL `pgvector` with HNSW Cosine Index  \n" \
                      f"**Embedding Model:** `{settings.AI_EMBEDDING_MODEL}` ({settings.AI_EMBEDDING_DIMENSIONS} dimensions)  \n" \
                      f"**Overall Mean Recall@5:** **{avg_recall}**\n\n" \
                      f"## Detailed Query Evaluation Table\n\n" \
                      f"| Test Query | Recall@5 | Top Retrieved Files |\n" \
                      f"| --- | --- | --- |\n"

        for row in eval_rows:
            retrieved_str = ", ".join(row["top_retrieved"]) if row["top_retrieved"] else "None"
            doc_content += f"| `{row['query']}` | {row['recall']} | {retrieved_str} |\n"

        with open(eval_doc_path, "w") as f:
            f.write(doc_content)

        self.stdout.write(self.style.SUCCESS(f"Updated benchmark evaluation results in {eval_doc_path}"))
