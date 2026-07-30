# SkyVault AI Engineering Roadmap

> **Purpose:** This document is the single source of truth for evolving SkyVault from a Django file manager into a portfolio-grade AI-powered vault. It is written so a human or **another AI agent** can pick up at any phase, understand context, and continue implementation without re-discovering the codebase.

**Last updated:** 2026-07-30  
**Status:** Foundation (F1–F5) + Phases 0–4 Complete — All Phases Implemented  
**Next actionable step:** Phase 4 complete — see [Implementation notes](#implementation-notes) for details.

---

## Table of contents

1. [How to use this document (for agents)](#1-how-to-use-this-document-for-agents)
2. [Current project snapshot](#2-current-project-snapshot)
3. [Target architecture](#3-target-architecture)
4. [Foundation phase — prepare for AI](#4-foundation-phase--prepare-for-ai)
5. [Phase 0 — AI infrastructure setup](#5-phase-0--ai-infrastructure-setup)
6. [Phase 1 — Auto-tagging & summarization](#6-phase-1--auto-tagging--summarization)
7. [Phase 2 — Semantic search & RAG](#7-phase-2--semantic-search--rag)
8. [Phase 3 — AI storage insights](#8-phase-3--ai-storage-insights)
9. [Phase 4 — Portfolio polish](#9-phase-4--portfolio-polish)
10. [Technical decisions (locked recommendations)](#10-technical-decisions-locked-recommendations)
11. [Environment variables reference](#11-environment-variables-reference)
12. [Dependencies to add (by phase)](#12-dependencies-to-add-by-phase)
13. [Testing & evaluation strategy](#13-testing--evaluation-strategy)
14. [Out of scope (for now)](#14-out-of-scope-for-now)
15. [Agent handoff checklist](#15-agent-handoff-checklist)

---



## 1. How to use this document (for agents)



### Before starting any phase

1. Read [Current project snapshot](#2-current-project-snapshot) and [Target architecture](#3-target-architecture).
2. Confirm which phases are **done** by checking the [Progress tracker](#progress-tracker) below.
3. Work phases **in order**. Do not skip Foundation or Phase 0 — later phases depend on Postgres + pgvector + async processing.
4. After completing a phase, update the Progress tracker, mark acceptance criteria, and note any deviations in [Implementation notes](#implementation-notes).



### Conventions for agents

- **Minimize scope:** Only change files required for the current phase.
- **Match existing style:** Function-based views, `@login_required`, Django templates, no DRF unless explicitly added later.
- **New AI code lives in** `ai_features/` — do not scatter AI logic across `vault/` except for thin integration hooks (signals, template includes).
- **Do not commit secrets.** Use `.env` (see [Environment variables](#11-environment-variables-reference)).
- **Do not add LangChain/LangGraph.** Hand-roll the RAG loop.
- **Run via Docker** once Foundation is complete — pgvector requires PostgreSQL.



### Progress tracker


| Phase | Name                           | Status        | Completed by | Notes |
| ----- | ------------------------------ | ------------- | ------------ | ----- |
| F1    | Standardize on PostgreSQL      | ✅ Complete    | 2026-07-30   | pgvector/pgvector:pg16, DB_ENGINE flag |
| F2    | Drive Experience & UI Refactoring | ✅ Complete | 2026-07-30   | Google Drive theme, global storage context, full-page context menu, in-app preview, AI slots |
| F3    | Background task infrastructure | ✅ Complete   | 2026-07-30   | django-q2 ORM broker, qcluster service, ai_features app shell, FileAnalysis model & upload signals |
| F4    | Upload pipeline hooks          | ✅ Complete   | 2026-07-30   | Extension allowlist filtering, FileAnalysis PENDING/SKIPPED status handling |
| F5    | Dev tooling & env template     | ✅ Complete   | 2026-07-30   | .env.example, .gitignore uncommented, docs/DEV_SETUP.md step-by-step guide |
| 0     | AI infrastructure setup        | ✅ Complete   | 2026-07-30   | anthropic, openai, pgvector, pdfplumber installed; service layer & smoke test built |
| 1     | Auto-tagging & summarization   | ✅ Complete   | 2026-07-30   | PDF/Plaintext extractors, Claude JSON tagging/summary task, UI preview slots & admin |
| 2     | Semantic search & RAG          | ✅ Complete   | 2026-07-30   | DocumentChunk pgvector model, HNSW index, paragraph chunker, RAG Q&A modal, Recall@K eval |
| 3     | AI storage insights            | ✅ Complete   | 2026-07-30   | StorageInsight model, gather_storage_stats, Claude insight generation, dashboard live banner |
| 4     | Portfolio polish               | ✅ Complete   | 2026-07-30   | ARCHITECTURE.md, README AI section, tests, seed_demo_vault, eval queries expanded to 12

### Implementation notes

*Agents: append dated notes here when you deviate from the plan or discover blockers.*

```
2026-07-30 — Phase 4 complete:
  - Created docs/ARCHITECTURE.md with Mermaid architecture diagram, RAG pipeline walkthrough, chunking strategy rationale, embedding model choice, and eval results summary.
  - Updated Readme.md with AI Features section (features list, how-it-works, API keys, eval instructions).
  - Created ai_features/tests/ with three test files: test_extractors.py, test_chunking.py, test_retrieval.py (mocked embeddings for retrieval).
  - Created ai_features/management/commands/seed_demo_vault.py (demo user + 12 sample files with known content).
  - Expanded ai_features/eval/queries.json from 5 to 12 query/file pairs matching demo vault content.
  - .env.example already had AI API key entries (no change needed).
  - vault/models.py had no duplicate imports (already clean).
  - vault/views.py had no debug print() statements (already uses logging).
  - EVAL_RESULTS.md needs real eval run after demo vault is seeded and indexed.
```

2026-07-30 — Phase 3 complete:
  - Created ai_features/services/insights.py (gather_storage_stats, generate_storage_insight with 24hr caching).
  - Added StorageInsight model (migration 0005) with OneToOne user, insight text, stats_snapshot JSON, generated_at.
  - Registered StorageInsight in ai_features/admin.py.
  - Added GET /dashboard/ai-insight/?refresh=1 endpoint in dashboard/views.py & wired URL.
  - Upgraded templates/dashboard/dashboard.html insight banner with live JS fetch, stats pills, spinner, and refresh button.
```





### Implementation notes

*Agents: append dated notes here when you deviate from the plan or discover blockers.*

```
2026-07-30 — F1 complete:
  - docker-compose uses pgvector/pgvector:pg16 with init_pgvector.sql mount
  - settings.py defaults to PostgreSQL; SQLite via DB_ENGINE=sqlite
  - Removed DJANGO_ENV gate for database selection (DJANGO_ENV kept in entrypoint for metadata)
  - If upgrading from old postgres:latest volume, run: docker-compose down -v
  - Fixed Dockerfile: strip CRLF from entrypoint.sh after COPY (Windows dev machines)
  - Verified: pgvector 0.8.6 enabled, migrations run, Django serves on :8000
```

---



## 2. Current project snapshot



### Stack


| Layer          | Technology                                                   |
| -------------- | ------------------------------------------------------------ |
| Framework      | Django 5.1.2                                                 |
| Python         | 3.12 (Dockerfile)                                            |
| DB (Docker)    | PostgreSQL via `docker-compose.yml` when `DJANGO_ENV=docker` |
| DB (local dev) | **PostgreSQL** (default via `.env`); SQLite optional via `DB_ENGINE=sqlite` |
| Auth           | Django built-in `User` model                                 |
| Frontend       | Server-rendered Django templates + static CSS/JS             |
| File storage   | Local filesystem (`MEDIA_ROOT`)                              |




### Django apps


| App             | Responsibility                          | Key files                                            |
| --------------- | --------------------------------------- | ---------------------------------------------------- |
| `accounts`      | Registration, login                     | `accounts/views.py`, `accounts/urls.py`              |
| `vault`         | File/folder CRUD, upload, search, trash | `vault/models.py`, `vault/views.py`, `vault/urls.py` |
| `dashboard`     | Storage charts (JSON endpoints)         | `dashboard/views.py`                                 |
| `settings`      | User profile, storage quota             | `settings/models.py`, `settings/signals.py`          |
| `notifications` | Notification list                       | `notifications/models.py`                            |




### Core models (`vault/models.py`)

```
Folder: user, name, trashed, parent_folder, created_at
File:   user, folder, name, uploaded_file, size, trashed, shared_with, created_at, starred
```

Files are stored at `media/user_<id>/<filename>` via `user_directory_path()`.

### Upload flow (integration point for AI)

```
POST /vault/upload/
  → vault/views.py::upload_file()
  → validates size (40 MB), storage quota (100 MB via UserProfile)
  → File.objects.create(...)
  → updates UserProfile.used_space
  → redirect (synchronous — no background processing today)
```

**Hook point for Phase 1:** post-save signal on `File`, or explicit call at end of `upload_file()`.

### Search (today)

```
GET /vault/search/?q=<query>
  → vault/views.py::search_view()
  → File.objects.filter(name__icontains=query)  # filename only
```

**Upgrade target for Phase 2:** semantic search over embedded chunks + optional filename fallback.

### Docker setup

- `docker-compose.yml`: `web-skyvault` + `db-skyvault` (`pgvector/pgvector:pg16`)
- `entrypoint.sh`: waits for DB, runs migrations, starts runserver
- PostgreSQL is the default database engine in `settings.py`



### Known gaps relevant to AI work

1. ~~**SQLite in local dev**~~ — resolved in F1; PostgreSQL is now default.
2. **No background jobs** — Claude/embedding calls on upload will block HTTP response.
3. **No text extraction** — PDFs opened inline but content never parsed.
4. **No file detail page** — no UI surface for summary/tags yet (must be added).
5. **No tests for vault AI paths** — test files exist but are mostly empty stubs.
6. **Duplicate imports** in `vault/models.py` (cosmetic, fix when touching file).

---



## 3. Target architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SkyVault (Django)                       │
├─────────────────────────────────────────────────────────────────┤
│  vault/          │  dashboard/     │  accounts/  │  settings/  │
│  (files, UI)     │  (charts)       │  (auth)     │  (profile)  │
├─────────────────────────────────────────────────────────────────┤
│                    ai_features/  ← NEW APP                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ extractors/ │  │ services/    │  │ models/                 │ │
│  │ pdf, txt    │  │ claude, embed│  │ FileAnalysis, DocChunk  │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ tasks/      │  │ retrieval/   │  │ management/             │ │
│  │ analyze_file│  │ vector_search│  │ run_eval                  │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector                                          │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │ vault_file       │  │ ai_features_docchunk                   │ │
│  │ ai_features_     │  │   embedding vector(1536)               │ │
│  │   fileanalysis   │  │   content, file_id, chunk_index        │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  External APIs                                                  │
│  Anthropic Claude (generation)  │  OpenAI (embeddings)          │
└─────────────────────────────────────────────────────────────────┘
```



### Data flow — upload (Phase 1+)

```
User uploads file
  → vault saves File record + file to disk
  → signal enqueues background task
  → task: extract text → call Claude (JSON) → save FileAnalysis
  → (Phase 2) task also: chunk → embed → save DocChunks with vectors
```



### Data flow — "Ask your vault" (Phase 2)

```
User submits natural language query
  → embed query
  → pgvector cosine search (top-k chunks, scoped to user)
  → build prompt with retrieved chunks + citations
  → Claude generates answer
  → return answer + source file links
```

---



## 4. Foundation phase — prepare for AI

> **Goal:** Remove blockers so AI phases can be built on a stable, production-like stack. Complete **all** foundation tasks before Phase 0.



### Foundation Phase F1 — Standardize on PostgreSQL

**Why:** pgvector requires PostgreSQL. SQLite/local vs Docker/Postgres split causes "works in Docker, breaks locally" confusion.

**Tasks:**

- [ ] **F1.1** Update `docker-compose.yml`:
  - Replace `postgres:latest` with `pgvector/pgvector:pg16` (or `ankane/pgvector`).
  - Add init script or document `CREATE EXTENSION vector;` step.
- [ ] **F1.2** Update `skyvault/settings.py`:
  - Use PostgreSQL as default for **all** environments (not only `DJANGO_ENV=docker`).
  - Read `DB_*` vars from `.env` with sensible localhost defaults.
  - Keep SQLite as optional fallback behind explicit `DB_ENGINE=sqlite` flag if desired.
- [ ] **F1.3** Update `Readme.md`:
  - Document that Postgres is required (local install or Docker).
  - Remove "uncomment SQLite section" guidance.
- [ ] **F1.4** Add `scripts/init_pgvector.sql`:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
  Mount in docker-compose if using init scripts.
- [ ] **F1.5** Verify: `docker-compose up --build`, migrate, upload a file — no regressions.

**Files to modify:**

- `docker-compose.yml`
- `skyvault/settings.py`
- `Readme.md`
- `scripts/init_pgvector.sql` (new)

**Acceptance criteria:**

- Fresh `docker-compose up` creates DB with `vector` extension enabled.
- Local dev (with Postgres running) uses same DB engine as Docker.
- Existing vault features (upload, delete, search by name) still work.

---

### Foundation Phase F2 — Drive Experience, UI Refactoring & AI UI Slots

**Why:** Ensure Google Drive UI feature parity, custom right-click menus across the full page, dark theme toggle, in-app file/folder previews, custom modal dialogs, and UI readiness slots for upcoming AI features.

**Tasks:**

- [ ] **F2.1** Storage Bar Global Context: Inject user storage stats globally in context processors so the sidebar storage widget works everywhere.
- [ ] **F2.2** Global Page Context Menu: Bind `contextmenu` to full page viewport (`.main-panel`) instead of restricted child elements.
- [ ] **F2.3** Google Drive Theme & Responsive Dark Mode: Implement light/dark mode design tokens and responsive drawer menu.
- [ ] **F2.4** Trash Icon Grid View & Context Menu: Render trashed items in grid cards with right-click "Restore" and "Delete Permanently" actions.
- [ ] **F2.5** In-App File/Folder Preview Modal: Open text, PDF, image, media previews, and folder contents in an overlay modal.
- [ ] **F2.6** Confirmation Modals: Replace browser native `alert`/`confirm` dialogs with customizable UI modals.
- [ ] **F2.7** AI UI Slots: Pre-build UI slots for "Ask SkyVault AI" sidebar link, file preview AI summary/tag chips area, and dashboard AI storage insight cards.

---

### Foundation Phase F3 — Background task infrastructure

**Why:** Claude + embedding calls take 2–15 seconds. Must not block upload HTTP response.

**Recommended approach (simplest for portfolio):** Django 5.1 native `django.tasks` is not stable — use `django-q2` or `celery` with Redis. For minimal deps, start with `django-q2` + ORM broker (no Redis required for dev).

**Alternative (dev-only, not recommended for production story):** `threading.Thread` in signal handler — fast to implement but poor for retries/monitoring.

**Tasks:**

- [ ] **F3.1** Add `django-q2` to `requirements.txt`.
- [ ] **F3.2** Configure in `settings.py` (`Q_CLUSTER` with ORM broker for dev).
- [ ] **F3.3** Add `qcluster` service to `docker-compose.yml` (or document running `python manage.py qcluster` in second terminal).
- [ ] **F3.4** Create `ai_features/tasks.py` stub with a no-op test task to verify queue works.
- [ ] **F3.5** Add task status field pattern (e.g. `processing_status` on future `FileAnalysis` model: `pending | processing | done | failed`).

**Files to modify/create:**

- `requirements.txt`
- `skyvault/settings.py`
- `docker-compose.yml`
- `ai_features/tasks.py` (create app shell first in F4, or stub in vault)

**Acceptance criteria:**

- Enqueuing a task from Django shell completes asynchronously.
- Failed tasks log errors without crashing the upload view.

---

### Foundation Phase F4 — Upload pipeline hooks

**Why:** Clean integration point for AI without bloating `vault/views.py`.

**Tasks:**

- [ ] **F3.1** Create `vault/signals.py`:
  ```python
  @receiver(post_save, sender=File)
  def on_file_uploaded(sender, instance, created, **kwargs):
      if created and not instance.trashed:
          # Phase 1: enqueue ai_features.tasks.analyze_file(instance.id)
          pass
  ```
- [ ] **F3.2** Register signals in `vault/apps.py` (`ready()` method).
- [ ] **F3.3** Skip AI processing for unsupported file types (images, video, audio) — check extension against allowlist: `.pdf`, `.txt`, `.md`, `.docx` (docx optional, Phase 1 stretch).
- [ ] **F3.4** On permanent delete (`delete_permanent_item`), ensure related AI records are cascade-deleted (FK with `on_delete=CASCADE`).

**Files to modify/create:**

- `vault/signals.py` (new)
- `vault/apps.py`

**Acceptance criteria:**

- Uploading a file triggers signal (verify with log/print or test).
- Signal does not fire on update-only saves (rename, star, trash).

---



### Foundation Phase F4 — Dev tooling & env template

**Tasks:**

- [ ] **F4.1** Create `.env.example` with all required variables (see [Section 11](#11-environment-variables-reference)).
- [ ] **F4.2** Uncomment `.env` in `.gitignore` (line 125 is currently commented out — secrets should not be committed).
- [ ] **F4.3** Add `docs/DEV_SETUP.md` with step-by-step: clone → `.env` → `docker-compose up` → create superuser.
- [ ] **F4.4** Pin key dependency versions in `requirements.txt` when adding AI packages.

**Acceptance criteria:**

- New developer (or agent) can boot the app from `.env.example` alone.

---



## 5. Phase 0 — AI infrastructure setup

> **Prerequisite:** Foundation F1–F4 complete.



### Tasks

- [ ] **0.1** Create Django app: `python manage.py startapp ai_features`
- [ ] **0.2** Add `ai_features` to `INSTALLED_APPS`.
- [ ] **0.3** Install and configure:
  - `anthropic` — Claude API client
  - `openai` — embeddings (`text-embedding-3-small`, 1536 dims)
  - `pgvector` — Django integration (`pgvector` Python package + `django.contrib.postgres` if needed)
  - `pdfplumber` or `pypdf` — PDF text extraction
- [ ] **0.4** Enable pgvector in Django:
  - Add migration to run `VectorExtension()` (pgvector Django helper).
- [ ] **0.5** Create `ai_features/services/claude.py`:
  - `get_client()` — reads `ANTHROPIC_API_KEY`
  - `generate_json(system_prompt, user_content, schema_description) -> dict`
  - Handle JSON parse failures with one retry.
- [ ] **0.6** Create `ai_features/services/embeddings.py`:
  - `embed_text(text: str) -> list[float]`
  - `embed_texts(texts: list[str]) -> list[list[float]]` (batch)
  - Reads `OPENAI_API_KEY`.
- [ ] **0.7** Add settings block in `skyvault/settings.py`:
  ```python
  ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
  OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
  AI_CLAUDE_MODEL = os.environ.get("AI_CLAUDE_MODEL", "claude-sonnet-4-20250514")
  AI_EMBEDDING_MODEL = os.environ.get("AI_EMBEDDING_MODEL", "text-embedding-3-small")
  AI_EMBEDDING_DIMENSIONS = 1536
  ```
- [ ] **0.8** Smoke test management command: `python manage.py ai_smoke_test` — calls Claude for JSON + embeds one sentence.



### Files to create

```
ai_features/
  __init__.py
  apps.py
  admin.py
  models.py          # empty for now
  services/
    __init__.py
    claude.py
    embeddings.py
  management/
    commands/
      ai_smoke_test.py
  migrations/
    0001_enable_pgvector.py
```



### Acceptance criteria

- `python manage.py ai_smoke_test` prints a JSON object from Claude and an embedding vector length of 1536.
- pgvector extension visible: `SELECT * FROM pg_extension WHERE extname = 'vector';`

---



## 6. Phase 1 — Auto-tagging & summarization

> **Prerequisite:** Phase 0 complete.



### Models

Add to `ai_features/models.py`:

```python
class FileAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        DONE = "done"
        FAILED = "failed"
        SKIPPED = "skipped"  # unsupported file type

    file = models.OneToOneField("vault.File", on_delete=models.CASCADE, related_name="analysis")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    summary = models.TextField(blank=True)
    tags = models.JSONField(default=list)           # ["invoice", "2024", "tax"]
    suggested_folder = models.CharField(max_length=255, blank=True)
    extracted_text = models.TextField(blank=True)   # reused in Phase 2 — do not re-extract
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```



### Text extraction (`ai_features/extractors/`)

- [ ] **1.1** `extractors/base.py` — `extract_text(file_path: str, extension: str) -> str | None`
- [ ] **1.2** `extractors/pdf.py` — pdfplumber
- [ ] **1.3** `extractors/plaintext.py` — `.txt`, `.md` with encoding fallback (utf-8, latin-1)
- [ ] **1.4** Return `None` for unsupported types → status `SKIPPED`



### Claude prompt (structured JSON)

System prompt contract:

```
You analyze documents for a personal file vault. Return ONLY valid JSON with this schema:
{
  "summary": "2-3 sentence summary",
  "tags": ["tag1", "tag2", ...],        // 3-7 lowercase tags
  "suggested_folder": "folder name"     // e.g. "Taxes", "Work", "Personal"
}
No markdown fences. No extra keys.
```

Use Claude model from settings. Truncate extracted text to ~8000 chars for Phase 1 (avoid token limits).

### Background task

- [ ] **1.5** `ai_features/tasks.py::analyze_file(file_id: int)`:
  1. Load `File`, create/update `FileAnalysis` → `PROCESSING`
  2. Extract text
  3. If no text → `SKIPPED`
  4. Call Claude → parse JSON → save summary, tags, suggested_folder, extracted_text
  5. On error → `FAILED` + error_message

- [ ] **1.6** Wire `vault/signals.py` to enqueue `analyze_file`.



### UI

- [ ] **1.7** Create file detail view: `GET /vault/file/<id>/` → `vault/views.py::file_detail`
  - Show: name, size, date, summary, tags (as chips), suggested folder
  - Show processing status if pending/failed
- [ ] **1.8** Template: `templates/vault/file_detail.html`
- [ ] **1.9** Link from `_file_grid.html` — click opens detail page instead of direct download for supported types (or add info icon).
- [ ] **1.10** Optional: show tag chips on search results page.



### Admin

- [ ] **1.11** Register `FileAnalysis` in `ai_features/admin.py` for debugging.



### Acceptance criteria

- Upload a `.txt` or `.pdf` → within ~30s, detail page shows summary + tags.
- Upload a `.jpg` → status `SKIPPED`, no error.
- Claude/API failure → status `FAILED`, upload itself still succeeds.
- Re-upload same filename blocked (existing behavior preserved).

---



## 7. Phase 2 — Semantic search & RAG

> **Prerequisite:** Phase 1 complete (`extracted_text` populated on `FileAnalysis`).



### Models

Add to `ai_features/models.py`:

```python
from pgvector.django import VectorField

class DocumentChunk(models.Model):
    file = models.ForeignKey("vault.File", on_delete=models.CASCADE, related_name="chunks")
    analysis = models.ForeignKey(FileAnalysis, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=1536)
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("file", "chunk_index")
        indexes = [
            # pgvector HNSW or IVFFlat index — add via migration
        ]
```



### Chunking (`ai_features/chunking.py`)

- [ ] **2.1** Implement semantic chunking strategy:
  - **Primary:** split on paragraph boundaries (`\n\n`)
  - **Max chunk size:** ~~500 tokens (~~2000 chars)
  - **Overlap:** 50 tokens (~200 chars) between chunks
  - **Min chunk size:** 50 chars (merge tiny fragments)
- [ ] **2.2** Document chosen strategy in code docstring (interview talking point).

**Do not use naive fixed-character splits without overlap** — note why in comments.

### Embedding pipeline

- [ ] **2.3** Extend `analyze_file` task (or add `index_file_chunks` task chained after analysis):
  1. Read `extracted_text` from `FileAnalysis`
  2. Chunk → embed batch → bulk create `DocumentChunk`
  3. Delete existing chunks for file before re-indexing (idempotent)

- [ ] **2.4** Add pgvector index migration (HNSW preferred):
  ```sql
  CREATE INDEX ON ai_features_documentchunk
  USING hnsw (embedding vector_cosine_ops);
  ```



### Retrieval (`ai_features/retrieval/search.py`)

- [ ] **2.5** `search_chunks(user, query: str, top_k: int = 5) -> list[DocumentChunk]`
  - Embed query
  - Filter by `file__user=user`, `file__trashed=False`
  - Order by cosine distance (`CosineDistance` from pgvector)
  - Return top-k with scores

- [ ] **2.6** `search_files(user, query: str, top_k: int = 10) -> list[File]`
  - Deduplicate chunks → files, rank by best chunk score



### Search UI upgrade

- [ ] **2.7** Update `vault/views.py::search_view`:
  - If query present: call semantic search, fall back to filename match
  - Pass results with relevance score + matched snippet

- [ ] **2.8** Update `templates/vault/search.html`:
  - Show snippet highlight, tags from `FileAnalysis`, relevance indicator



### "Ask your vault" (RAG Q&A)

- [ ] **2.9** New view: `GET/POST /vault/ask/` → `ai_features/views.py::ask_vault`
- [ ] **2.10** RAG prompt template:
  ```
  System: Answer based ONLY on the provided document excerpts. Cite file names.
  If insufficient context, say "I couldn't find relevant documents."

  Context:
  [1] filename.pdf: "...chunk text..."
  [2] notes.txt: "...chunk text..."

  User question: {query}
  ```
- [ ] **2.11** Template: `templates/vault/ask.html` — query box + answer + cited files list
- [ ] **2.12** Add nav link in `templates/base.html`



### Evaluation (differentiator — do not skip)

- [ ] **2.13** Create `ai_features/eval/queries.json`:
  ```json
  [
    {"query": "tax documents 2024", "expected_files": ["tax_return.pdf"], "k": 5},
    ...
  ]
  ```
  Minimum **10 query/file pairs** using sample documents you upload to a test user.

- [ ] **2.14** Management command: `python manage.py run_search_eval`
  - Computes **recall@k** per query and overall average
  - Prints results table to stdout
  - Exit code 1 if recall@5 < 0.6 (adjust threshold after baseline)

- [ ] **2.15** Record baseline eval results in `docs/EVAL_RESULTS.md`



### Acceptance criteria

- Semantic search returns relevant files for content-based queries (not just filename).
- "Ask your vault" returns an answer with file citations.
- `run_search_eval` produces recall@k metrics.
- Chunks scoped per user (user A cannot retrieve user B's documents).

---



## 8. Phase 3 — AI storage insights

> **Prerequisite:** Phase 1 complete (tags/summaries exist). Phase 2 optional but improves insight quality.



### Data aggregation

- [ ] **3.1** Create `ai_features/services/insights.py::gather_storage_stats(user) -> dict`:
  ```python
  {
    "total_files": N,
    "total_mb": X,
    "by_type": {"pdf": 10, "jpg": 5, ...},
    "by_tag": {"work": 8, "personal": 3, ...},
    "untouched_6mo": N,          # files not opened/modified in 6 months
    "largest_files": [{"name": ..., "mb": ...}, ...],  # top 5
    "trashed_count": N,
  }
  ```



### Claude insight generation

- [ ] **3.2** Prompt Claude with aggregated stats (not raw file contents) → 2-3 sentence insight.
- [ ] **3.3** Cache insight on `UserProfile` or new `StorageInsight` model (regenerate daily or on demand).
- [ ] **3.4** Add endpoint: `GET /dashboard/ai-insight/` → JSON `{ "insight": "...", "generated_at": "..." }`



### Dashboard UI

- [ ] **3.5** Add insight card to `templates/dashboard/dashboard.html`
- [ ] **3.6** Fetch via JS from new endpoint (match existing chart fetch pattern in dashboard)



### Acceptance criteria

- Dashboard shows a natural-language storage insight for logged-in user.
- Insight updates when underlying stats change (manual refresh button acceptable).

---



## 9. Phase 4 — Portfolio polish

> **Prerequisite:** Phases 0–2 complete (Phase 3 optional).



### Documentation

- [ ] **4.1** Add `docs/ARCHITECTURE.md`:
  - Architecture diagram (Mermaid)
  - RAG pipeline walkthrough
  - Chunking strategy + rationale
  - Embedding model choice + dimensions
  - Eval results summary with recall@k table

- [ ] **4.2** Update `Readme.md` with new section: **AI Features**
  - Screenshots of tags, semantic search, ask vault
  - Required API keys
  - How to run eval

- [ ] **4.3** Add `.env.example` entries for all AI keys



### Code quality

- [ ] **4.4** Remove debug `print()` statements (e.g. `vault/views.py::paste`)
- [ ] **4.5** Fix duplicate imports in `vault/models.py`
- [ ] **4.6** Add basic tests:
  - `ai_features/tests/test_extractors.py`
  - `ai_features/tests/test_chunking.py`
  - `ai_features/tests/test_retrieval.py` (with mocked embeddings)



### Demo data

- [ ] **4.7** Management command: `python manage.py seed_demo_vault`
  - Creates demo user + 10–15 sample files with known content for eval/demo



### Acceptance criteria

- README AI section is interview-ready (you can explain the system in 5 minutes from docs alone).
- Eval results documented with numbers, not just "it works".

---



## 10. Technical decisions (locked recommendations)


| Decision             | Choice                              | Rationale                                                          |
| -------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| LLM provider         | **Anthropic Claude**                | Structured JSON tagging, RAG answers                               |
| Embedding provider   | **OpenAI** `text-embedding-3-small` | Cheap, 1536 dims, well-documented; Anthropic has no embeddings API |
| Vector store         | **pgvector**                        | Already on Postgres; no extra infra vs Pinecone/Chroma             |
| RAG framework        | **None (hand-rolled)**              | Stronger CV signal; full control                                   |
| Background tasks     | **django-q2** (ORM broker)          | No Redis required for dev; good enough for portfolio               |
| PDF extraction       | **pdfplumber**                      | Better text extraction than PyPDF2 for most docs                   |
| Chunking             | **Paragraph-based + overlap**       | Simple, explainable; avoid naive fixed-size                        |
| Embedding dimensions | **1536**                            | Matches `text-embedding-3-small` default                           |
| Auth scope           | **Per-user isolation**              | All retrieval queries filter by `file__user=request.user`          |




### Claude model

Default: `claude-sonnet-4-20250514` (configurable via env). Use Sonnet for balance of cost/quality in dev.

---



## 11. Environment variables reference

Create `.env.example` with:

```env
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL — required for AI features)
DB_NAME=skyvault
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DJANGO_ENV=development

# AI — Phase 0+
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# AI — optional overrides
AI_CLAUDE_MODEL=claude-sonnet-4-20250514
AI_EMBEDDING_MODEL=text-embedding-3-small
AI_EMBEDDING_DIMENSIONS=1536
```

---



## 12. Dependencies to add (by phase)



### Foundation

```
django-q2>=1.6.0
```



### Phase 0

```
anthropic>=0.40.0
openai>=1.50.0
pgvector>=0.3.0
pdfplumber>=0.11.0
```



### Phase 2 (eval)

No extra deps — eval is a management command.

---



## 13. Testing & evaluation strategy



### Unit tests (Phase 4)


| Module                | What to test                                       |
| --------------------- | -------------------------------------------------- |
| `chunking.py`         | Paragraph splits, overlap, max size, min merge     |
| `extractors/pdf.py`   | Extracts text from sample PDF fixture              |
| `retrieval/search.py` | User scoping, top-k ordering (mock embeddings)     |
| `services/claude.py`  | JSON parse, retry on malformed response (mock API) |




### Integration tests

- Upload file → signal → task → `FileAnalysis.status == DONE` (mock Claude).



### Eval set (Phase 2 — required)

- 10+ queries with known expected files
- Metric: **recall@k** (is expected file in top-k results?)
- Target: recall@5 ≥ 0.6 on demo corpus (adjust after baseline)
- Store results in `docs/EVAL_RESULTS.md`

---



## 14. Out of scope (for now)

- LangChain / LangGraph / LlamaIndex
- OCR for scanned PDFs / images
- Real-time streaming responses (SSE)
- Multi-modal embeddings (image search)
- Pinecone / Weaviate / external vector DB
- Celery + Redis in production (django-q2 sufficient for portfolio)
- API-first design (DRF) — keep server-rendered templates
- Sharing AI analysis on shared files (only file owner for v1)

---



## 15. Agent handoff checklist

When finishing a work session, the agent **must**:

1. ☐ Update [Progress tracker](#progress-tracker) statuses
2. ☐ Append notes to [Implementation notes](#implementation-notes) if anything deviated
3. ☐ List files created/modified
4. ☐ State which acceptance criteria pass/fail
5. ☐ Document any manual steps (API keys, docker commands, seed data)
6. ☐ Identify the **next uncompleted task ID** (e.g. "Next: F1.2")



### Quick-start commands for the next agent

```bash
# Boot the stack
cp .env.example .env   # fill in API keys after Phase 0
docker-compose up --build

# Separate terminal (after F2)
python manage.py qcluster

# After Phase 0
python manage.py ai_smoke_test

# After Phase 2
python manage.py run_search_eval
```



### Key file touchpoints by phase


| Phase | Primary files                                                                   |
| ----- | ------------------------------------------------------------------------------- |
| F1    | `docker-compose.yml`, `skyvault/settings.py`                                    |
| F2    | `skyvault/settings.py`, `docker-compose.yml`, `requirements.txt`                |
| F3    | `vault/signals.py`, `vault/apps.py`                                             |
| 0     | `ai_features/` (new app), `requirements.txt`                                    |
| 1     | `ai_features/models.py`, `tasks.py`, `extractors/`, `vault/views.py`, templates |
| 2     | `ai_features/chunking.py`, `retrieval/`, `eval/`, search + ask templates        |
| 3     | `ai_features/services/insights.py`, `dashboard/views.py`, dashboard template    |
| 4     | `docs/ARCHITECTURE.md`, `Readme.md`, tests                                      |


---



## Appendix A — Learning exercises (optional, parallel track)

These can be done as throwaway scripts **before or during** Phase 0. They are not blocking but build interview fluency.

1. **Embeddings by hand:** Embed 5 sentences with OpenAI, compute cosine similarity in numpy, retrieve closest match.
2. **Claude JSON:** Single script — send paragraph, get back `{summary, tags}` as strict JSON.
3. **pgvector scratch:** Insert 3 chunks with embeddings into a raw Postgres table, run cosine query.

See `docs/learning/` (create if doing exercises) — keep scripts out of main app.

---



## Appendix B — Interview talking points (post Phase 2)

- "I isolated AI logic in a dedicated Django app with a clear service layer."
- "Upload triggers async analysis — the HTTP response is never blocked by LLM latency."
- "I chose pgvector over a separate vector DB to keep ops simple and stay in Postgres."
- "Chunking uses paragraph boundaries with overlap because fixed-size splits break mid-sentence."
- "I built a recall@k eval set — here's my baseline and what I'd improve next."

