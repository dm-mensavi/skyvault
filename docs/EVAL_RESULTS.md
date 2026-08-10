# SkyVault AI — Retrieval & RAG Benchmark Results

**Evaluated on:** 2026-07-30  
**Vector Store:** PostgreSQL `pgvector` with HNSW Cosine Index  
**Embedding Model:** `all-MiniLM-L6-v2` (384 dimensions)  
**Overall Mean Recall@5:** **0.0**

> **These numbers are invalid — do not cite them.** This run was made while
> `AI_EMBEDDING_MODEL` was still set to the OpenAI id `text-embedding-3-small`,
> which sentence-transformers could not load. Every query embedded to `[]`, so
> retrieval returned nothing and every row scored 0.0. This reflects a
> misconfiguration, not retrieval quality. Re-run `python manage.py run_search_eval`
> after backfilling with `reindex_embeddings` to regenerate this file.

## Detailed Query Evaluation Table

| Test Query | Recall@5 | Top Retrieved Files |
| --- | --- | --- |
| `invoice billing payment` | 0.0 | None |
| `resume curriculum vitae work history` | 0.0 | None |
| `calendar schedule academic year` | 0.0 | None |
| `code interactive final engineering` | 0.0 | None |
| `cover letter job application` | 0.0 | None |
