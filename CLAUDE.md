# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkyVault is a Django 5.1 personal file vault with AI-powered features: auto-tagging, semantic search, RAG Q&A, and storage insights. The AI pipeline is hand-rolled (no LangChain) for portfolio differentiation and full control.

**Tech Stack:**
- Django 5.1 with PostgreSQL 16 + pgvector extension
- django-q2 for async background tasks (ORM broker, no Redis)
- Anthropic Claude for text generation (analysis, summarization, RAG)
- Local sentence-transformers embeddings (`all-MiniLM-L6-v2`, 384 dims) for semantic search — no API key required
- Server-rendered templates (no DRF/SPA)

## Development Commands

### Docker (Recommended)

```bash
# Start all services (web + db + qcluster worker)
docker-compose up --build

# Run migrations
docker-compose exec web-skyvault python manage.py migrate

# Create superuser
docker-compose exec web-skyvault python manage.py createsuperuser

# Django shell
docker-compose exec web-skyvault python manage.py shell

# View logs
docker-compose logs -f web-skyvault    # Django web server
docker-compose logs -f qcluster        # Background task worker

# Stop everything
docker-compose down

# Reset database volume (required if pgvector init script didn't run)
docker-compose down -v
```

### Local Development

```bash
# Activate virtualenv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver

# Start background worker (required for AI features - run in separate terminal)
python manage.py qcluster
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test ai_features
python manage.py test ai_features.tests.test_chunking

# Run specific test class
python manage.py test ai_features.tests.test_chunking.TestChunking

# Run specific test method
python manage.py test ai_features.tests.test_chunking.TestChunking.test_paragraph_split
```

Tests use Django's `TestCase`. Key test files:
- `ai_features/tests/test_chunking.py` - Chunking logic
- `ai_features/tests/test_retrieval.py` - Semantic search
- `ai_features/tests/test_extractors.py` - PDF/text extraction

### AI Feature Commands

```bash
# Verify API keys and test Claude generation + local embedding connectivity
python manage.py ai_smoke_test

# Run semantic search evaluation benchmark (Recall@K)
python manage.py run_search_eval

# Rebuild vector chunks from already-extracted text (no re-extraction, no Claude calls).
# Needed after an embedding-model change, since analyze_file only runs on upload.
python manage.py reindex_embeddings              # all files
python manage.py reindex_embeddings --user alice # scope to one user
python manage.py reindex_embeddings --force      # redo files that already have chunks

# Seed demo vault with sample files for testing
python manage.py seed_demo_vault
```

## Architecture

### Core Apps

- **vault/** - File/folder CRUD, upload handling, trash, starred items, context menu actions
- **ai_features/** - AI models, background tasks, text extraction, embeddings, semantic search, RAG
- **accounts/** - User authentication and profile management
- **settings/** - User preferences (theme, storage limits)
- **dashboard/** - Storage overview, activity widgets, AI-generated insights
- **notifications/** - User notification system

### AI Pipeline Flow

1. **Upload** → User uploads `.pdf`, `.txt`, `.md`, etc.
2. **Signal** → `vault/signals.py` `post_save` enqueues `ai_features.tasks.analyze_file(file_id)` via django-q2
3. **Extract** → `ai_features/extractors/` dispatch:
   - `pdf.py` uses `pdfplumber`
   - `plaintext.py` handles `.txt`, `.md`, `.json`, `.py`, `.js`, `.html`, `.css`, `.csv`, `.xml`
4. **Analyze** → Truncated text (8000 chars) sent to Claude → returns JSON with `summary`, `tags`, `suggested_folder`
5. **Chunk** → `ai_features/chunking.py` splits full text using paragraph boundaries with 200-char overlap, max 2000 chars/chunk
6. **Embed** → Each chunk embedded locally via sentence-transformers → stored in `DocumentChunk` with pgvector `VectorField`
7. **Search** → User query → embedded → cosine distance search via pgvector HNSW index → deduplicated to files
8. **RAG** → Retrieve top-5 chunks → build context with citations → send to Claude → generate grounded answer

### Key Design Patterns

**Chunking Strategy:**
- Paragraph-based (splits on `\n\n`) to preserve semantic units
- Max 2000 chars, 200-char overlap between chunks
- Long paragraphs sub-split on sentence boundaries
- Tiny fragments (<50 chars) merged with preceding chunk
- See `ai_features/chunking.py` and `docs/ARCHITECTURE.md` for rationale

**Two-Tier Generation:**
- Primary: `ANTHROPIC_API_KEY` + `ANTHROPIC_BASE_URL` (supports custom gateways like AgentRouter)
- Fallback: `AI_FALLBACK_MODEL` + `AI_FALLBACK_API_KEY` (optional secondary model)
- Both use Anthropic-compatible `/v1/messages` API
- See `ai_features/services/claude.py`

**Per-User Isolation:**
- All retrieval queries filter by `file__user=request.user`
- Files and folders scoped to authenticated user
- Background tasks preserve user context

**Background Task Broker:**
- django-q2 uses Django ORM as task queue (no Redis)
- Sufficient for portfolio scale
- `qcluster` worker must run alongside web server

### Environment Variables

Required for AI features (set in `.env`):

```env
# Generation (Anthropic-compatible endpoint)
ANTHROPIC_AUTH_TOKEN=sk-...
ANTHROPIC_BASE_URL=https://agentrouter.org  # or empty for api.anthropic.com
ANTHROPIC_MODEL=claude-opus-5

# Embeddings — local sentence-transformers, no API key needed.
# Defaults to all-MiniLM-L6-v2 (384 dims); override only to change model.
AI_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Optional fallback generation
AI_FALLBACK_MODEL=gpt-5.6-sol
AI_FALLBACK_API_KEY=sk-...
AI_FALLBACK_BASE_URL=https://agentrouter.org

# Database (PostgreSQL required for AI features)
DB_NAME=skyvault
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost  # or db-skyvault in Docker
DB_PORT=5432
```

**SQLite Fallback:** Set `DB_ENGINE=sqlite` to disable pgvector and AI features (legacy dev mode only).

### Important Files

- `skyvault/settings.py` - Django settings, AI config loaded from env vars
- `ai_features/tasks.py` - Background task entry point (`analyze_file`)
- `ai_features/services/claude.py` - Generation client with fallback
- `ai_features/services/embeddings.py` - Local sentence-transformers embedding client
- `ai_features/services/search.py` - Semantic search over pgvector
- `ai_features/services/insights.py` - Dashboard AI insights
- `ai_features/models.py` - `FileAnalysis`, `DocumentChunk`, `StorageInsight`
- `vault/signals.py` - Triggers AI analysis on file upload
- `vault/views.py` - File/folder CRUD, upload, search
- `ai_features/views.py` - RAG Q&A endpoint (`/vault/ask/`)

### Migrations

pgvector setup is handled via migrations:
- `ai_features/migrations/0002_enable_pgvector.py` - Enables `vector` extension
- `ai_features/migrations/0003_documentchunk.py` - Creates `DocumentChunk` with `VectorField`
- `ai_features/migrations/0004_hnsw_index.py` - Creates HNSW index for cosine distance

Fresh Docker deployment auto-runs `scripts/init_pgvector.sql` on db init.

## Common Workflows

### Adding a New File Extractor

1. Create `ai_features/extractors/yourformat.py` implementing `extract_text(file_path: str) -> str`
2. Update `ai_features/extractors/base.py` `extract_text()` dispatcher to route new extensions
3. Add tests in `ai_features/tests/test_extractors.py`

### Modifying AI Analysis Schema

1. Update prompt in `ai_features/tasks.py` `analyze_file()`
2. Adjust `FileAnalysis` model fields if needed (requires migration)
3. Update `vault/templates/vault/file_detail.html` to display new fields

### Debugging Background Tasks

- Check `docker-compose logs -f qcluster` or local `python manage.py qcluster` output
- Inspect `django_q_*` tables in database for task state
- Use `ai_smoke_test` to verify API connectivity before debugging pipeline

### Running Evaluation

Benchmark queries are in `ai_features/eval/queries.json`. Run:
```bash
python manage.py run_search_eval
```
Results written to `docs/EVAL_RESULTS.md`.

## Documentation

- `Readme.md` - Project overview, setup instructions, AI features
- `docs/ARCHITECTURE.md` - Detailed architecture diagram (Mermaid), RAG pipeline, design decisions
- `docs/DEV_SETUP.md` - Developer setup guide
- `docs/ROADMAP.md` - Future feature plans
- `docs/EVAL_RESULTS.md` - Retrieval evaluation results (Recall@K)

## Type Checking

Pyrefly config in `pyrefly.toml` points to `.venv/Scripts/python.exe` for site-packages resolution.
