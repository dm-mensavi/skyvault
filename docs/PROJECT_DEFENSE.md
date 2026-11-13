# SkyVault — Project Defense Guide

This guide is a code-based explanation of what SkyVault currently does, why its
main design choices were made, how to demonstrate it, and where its limits are.
Use it to prepare a presentation, project defense, or technical interview.

## 1. Short project pitch

> SkyVault is a Django-based personal file vault that combines ordinary file
> organization with AI-assisted document understanding. It extracts text from
> supported uploads, generates summaries and tags asynchronously, indexes
> document passages as local embeddings in PostgreSQL/pgvector, and uses
> retrieval-augmented generation (RAG) to answer questions with file citations.
> It is a portfolio-scale, single-application prototype, not a production
> cloud-storage service.

### The problem and the response

As a vault accumulates documents, finding a particular fact by filename or
folder becomes inconvenient. SkyVault addresses this with:

- Familiar file and folder operations (upload, organize, preview, download,
  star, trash, restore, and search).
- Automatic metadata suggestions (summary, tags, suggested folder).
- Semantic retrieval, so a query can find passages even when its wording differs
  from the document.
- A dashboard that summarizes storage usage and offers an AI-generated storage
  insight.

The AI features augment file management; they do not replace the database,
permissions, or file storage layer.

## 2. Stack and why it was chosen

| Layer | Implementation | Defense rationale and trade-off |
|---|---|---|
| Language/runtime | Python 3.12 | Mature ecosystem for Django, document processing, OCR, embeddings, and AI integration. |
| Web framework | Django 5.1 | Integrated routing, ORM, authentication, forms, CSRF protection, templates, migrations, and admin reduce the amount of infrastructure code for a server-rendered app. |
| UI | Django templates, HTML, CSS, and vanilla JavaScript; Tailwind CSS build tooling; Chart.js for dashboard charts | Keeps the app as one deployable application without a separate SPA/API stack. The trade-off is that richer client-side interactions are hand-written. |
| Relational database | PostgreSQL 16 | Stores users, folders, files, analysis records, task-queue records, and vector chunks in one database. |
| Vector search | pgvector with a cosine HNSW index | Adds vector retrieval to the existing PostgreSQL deployment without introducing a separate vector database. |
| Background work | django-q2 with the Django ORM broker | Upload-triggered AI work can run in a worker instead of holding the web request open. ORM broker is simple for a small deployment and avoids Redis; it is not intended as a high-throughput distributed queue. |
| Document extraction | pdfplumber, python-docx/docx2txt, Python text readers, Pillow, pytesseract/Tesseract | Uses format-specific tools; OCR runs locally, while text generation uses an external compatible API. Extraction quality depends on the source file. |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2`, 384 dimensions | Local inference avoids per-query embedding API charges and keeps document embeddings under application control. The trade-off is model-loading and CPU cost. |
| Text generation | Anthropic-compatible Messages API via a configurable endpoint and model | Uses a hosted language model for summaries, tags, suggested folders, RAG answers, and storage insights. It introduces network latency, provider availability, model-access, and usage-cost dependencies. |
| Packaging | Docker Compose: Django web service, django-q2 worker, PostgreSQL/pgvector | Provides repeatable local development and keeps the database/extension setup consistent. The current Compose setup is for development, not a hardened public deployment. |

### Why not a separate frontend or REST API?

The product's current workflows are served by Django templates plus focused
JavaScript requests. That avoids maintaining a second application and an API
contract for a single-user-facing portfolio project. A separate frontend could
be justified later if independent clients or a larger client-side product
become requirements.

### Why PostgreSQL plus pgvector instead of a vector database?

The app already needs a relational database for ownership, folders, files, and
analysis state. pgvector keeps metadata and embeddings together and allows
ordinary SQL filters (including per-user and non-trashed-file filters) alongside
nearest-neighbor search. A dedicated vector service could be appropriate at
larger scale, but would add another service, data synchronization, and
operational complexity without a demonstrated need here.

## 3. Architecture at a glance

```text
Browser
  | Django pages and file/AI requests
  v
Django web service ----------------------> Generation API
  |                                           (compatible Messages API)
  | File/analysis/task records
  v
PostgreSQL + pgvector <----------------- Django-Q2 worker
  |                                        | extract text/OCR
  | vectors and relational data           | chunk and embed locally
  |                                        | request summary/tags/folder
  +----------------------------------------+

Uploaded file bytes are stored in the application's local media directory.
```

The main Django apps are:

- `vault/`: files, folders, uploads, previews, organization, search, trash, and
  file-serving views.
- `ai_features/`: analysis and vector models, extraction, chunking, embeddings,
  retrieval, RAG, storage insight, and AI diagnostics.
- `accounts/`: registration and login using Django's built-in user model.
- `settings/`: profile and storage-quota data.
- `dashboard/`: storage charts and the cached AI insight endpoint.
- `notifications/`: notification views and records.

### Important data models

- `File` belongs to a Django user, can belong to a folder, and stores an
  `uploaded_file` path, filename, byte size, category, trash/star state, and
  optional `shared_with` users.
- `Folder` belongs to a user and can have a parent folder, enabling a hierarchy.
- `FileAnalysis` is one-to-one with a file. It stores a lifecycle status,
  extracted text, summary, tags, suggested folder, and any error message.
- `DocumentChunk` belongs to a file and its analysis. It stores chunk text,
  sequence number, approximate token count, and a 384-dimensional embedding.
- `StorageInsight` caches one insight and statistics snapshot per user.
- `UserProfile` stores used space and defines the prototype's 100 MiB quota.

## 4. End-to-end methodology

### 4.1 Upload and organization

1. An authenticated user uploads one or more files. The view enforces a
   40 MiB-per-file maximum, checks the profile's 100 MiB quota, and rejects
   audio/video extensions and matching MIME types.
2. The file is saved under a user-specific directory in local media storage and
   represented by a `File` row.
3. A `post_save` signal creates a `FileAnalysis` record and enqueues
   `ai_features.tasks.analyze_file(file_id)` for supported extensions. Other
   types are marked `SKIPPED`.
4. The upload view also attempts text extraction synchronously for its
   deterministic, keyword-based initial category/folder placement. This improves
   the immediate upload UX, but means upload is not entirely non-blocking; the
   background task performs extraction again for analysis.
5. Once AI analysis completes, its suggested folder can move the file to a
   user-owned folder with that name.

The system's initial category rules are ordinary code, not an LLM classifier.
The later suggested-folder result is generated by the language model. Being
clear about this distinction is useful in a defense. The upload view blocks
audio/video but does not enforce a general extension allowlist; the signal's
AI-processing allowlist determines which uploaded extensions are actually
queued for analysis.

### 4.2 Extraction, analysis, and indexing

The background analysis lifecycle is:

```text
PENDING -> PROCESSING -> DONE | SKIPPED | FAILED
```

- PDF: pdfplumber extracts text. For PDFs longer than ten pages, the current
  extractor samples the first five and last five pages; middle pages are not
  indexed. Scanned PDFs are not OCR'd by this PDF path.
- DOCX/DOC: python-docx or docx2txt extracts text; DOCX tables are included.
- Images: the extractor implements pytesseract with the local Tesseract binary
  for English OCR. However, image extensions are currently absent from the
  upload signal's AI-processing allowlist, so uploaded images are marked
  `SKIPPED` rather than sent through the background AI pipeline. The extractor
  exists, but this path is not yet wired end to end.
- Plain text: supported formats include TXT, Markdown, JSON, Python, JavaScript,
  HTML, CSS, CSV, and XML, with encoding fallbacks.
- Audio and video are blocked at upload.

The worker stores the extracted text, chunks and embeds the full extracted
text, then sends up to 4,000 characters to the generation model for a structured
JSON result: summary, tags, and suggested folder. Therefore, the indexed text
can include content beyond the portion used to generate the summary and tags.

### 4.3 Data handling and privacy boundary

- Embedding inference runs locally in the application process. Document vectors
  are stored in PostgreSQL; query vectors are generated in memory for retrieval.
- The extracted document text (up to 4,000 characters per analysis request) is
  sent to the configured external generation endpoint for metadata generation.
- RAG sends retrieved text excerpts, filenames, and the user's question to that
  endpoint for answer generation.
- Storage-insight generation sends aggregated statistics, top tags, and names
  of the largest files; it does not need to send full file contents for that
  feature.
- The application code does not establish or control the external provider's
  retention/training policy. For real private data, confirm the provider's data
  terms and configure an appropriate endpoint before use.

Use synthetic or explicitly shareable documents in a demo.

### 4.4 Chunking and embedding choices

`ai_features/chunking.py` uses:

- Paragraph boundaries (`\n\n`) as the first split, preserving more semantic
  structure than fixed-size slicing.
- A 2,000-character maximum chunk size.
- A 200-character overlap to retain context around boundaries.
- Sentence-boundary splitting for long paragraphs where possible.
- Merging of trailing fragments shorter than 50 characters when the maximum
  chunk size permits.

The overlap reduces the chance that a useful phrase falls across a boundary,
but increases duplicate text and embedding count. Character counts are
approximations, not tokenizer-exact token limits.

`all-MiniLM-L6-v2` maps each chunk and query to a 384-dimensional vector.
Embeddings are generated inside the application process and stored in pgvector.
The Dockerfile installs CPU-only PyTorch; Apple MPS or AMD ROCm acceleration is
not enabled by the current Docker configuration.

### 4.5 Semantic retrieval and RAG

For a document question:

1. The query is embedded using the same local embedding model.
2. pgvector orders the requesting user's non-trashed chunks by cosine distance
   and returns up to five chunks.
3. The application converts cosine distance to a similarity score and keeps
   chunks at or above the current 0.35 threshold.
4. It sends the surviving excerpts, filenames, and question to the generation
   model with instructions to answer from the excerpts and cite sources as
   `[1]`, `[2]`, etc.
5. The response is returned with only source files whose index appears in the
   answer.

Retrieval is scoped by `file__user=request.user` and excludes trashed files.
This is the key access-control boundary for RAG; the model receives only the
selected excerpts, not direct database access.

Simple phrases classified as chitchat bypass vector search and use a separate
general conversation prompt. The endpoint is single-turn: it does not send the
browser's previous chat history to the model.

RAG grounding and citations reduce unsupported answers but cannot guarantee
that a model will never hallucinate or cite incorrectly. If there are no
relevant chunks, the system uses the general prompt; that prompt instructs the
model to say when a personal-file answer cannot be found.

### 4.6 Storage insight

The dashboard aggregates per-user statistics (file counts, bytes, extensions,
AI tags, largest files, files older than six months, and trash count). It
generates a short recommendation and caches the result for 24 hours unless the
user explicitly refreshes it. An empty vault receives a deterministic message
without calling the model.

## 5. Methodology decisions to defend

### Retrieval-augmented generation rather than fine-tuning

The app's knowledge is each user's changing private document collection.
Retrieval makes that content available at query time without training a model
on it, and permits citations back to stored files. Fine-tuning is better suited
to changing model behavior or style than frequently changing per-user facts.
RAG still needs careful relevance evaluation and privacy controls.

### Separate embeddings from generation

Embeddings need consistent vectors and fast local inference; generation needs
flexible language reasoning. Using a local embedding model and a configurable
hosted generation model keeps those responsibilities independent. The trade-off
is that both libraries, a local model cache, and an external generation
credential must be operated.

### Asynchronous analysis

Extraction, embedding, and generation can be much slower than saving a file.
Queueing analysis lets the upload flow return without waiting for all AI steps,
and status fields make progress/failure visible. The current ORM-backed
django-q2 broker is intentionally simple; a larger deployment would likely use
a more scalable broker and explicit monitoring/retry policy.

### Why a hand-built RAG pipeline?

The pipeline is short enough to implement directly: embed, retrieve, construct
a prompt, generate, and attach citations. Owning those steps makes it easier to
show where filtering, thresholds, prompts, and citations are applied, while
avoiding a large orchestration dependency. This favors transparency and control
over framework-provided abstractions.

## 6. Evaluation and testing: what can be claimed

Automated tests currently cover chunking, extraction dispatch/PDF sampling,
retrieval behavior and user filtering, upload categorization, AI response
handling, and empty-generation diagnostics. Provider calls and embeddings are
mocked in relevant tests so most tests do not require a live API key. The
retrieval tests still require a database setup compatible with pgvector.

Useful commands:

```bash
python manage.py test
python manage.py test ai_features
python manage.py ai_smoke_test
python manage.py run_search_eval
```

The smoke test checks the pgvector extension, configured generation endpoint,
fallback endpoint (if configured), and whether local embeddings return a
384-dimensional vector. It is an integration/configuration check, not an
answer-quality benchmark.

**Do not claim the existing `docs/EVAL_RESULTS.md` score as evidence of search
quality.** That report explicitly says its recorded zero score came from an
invalid embedding-model configuration. Also, the current evaluation command
uses a small query set and tests expected keywords against retrieved filenames;
it is a rough sanity check, not a human-judged semantic relevance benchmark.
It selects the first database user, so evaluation quality depends on which
user's files are present.

A defensible next evaluation would:

1. Re-index a known, clean corpus using the configured 384-dimensional model.
2. Create manually judged query-to-relevant-document labels, independent of
   filenames.
3. Report Recall@K and a ranking metric such as MRR or nDCG on a held-out query
   set, with corpus size and configuration recorded.
4. Separately measure retrieval latency and end-to-end answer latency.
5. Inspect a sample of answers and citations for grounding and correctness.

Until that is done, describe evaluation as a planned/rough benchmark and present
the behavior demonstrated, not an unsupported quality percentage.

## 7. Limitations and honest boundaries

- This is a local-file-storage prototype, not a multi-region or managed cloud
  drive. The Docker PostgreSQL volume persists database data; uploaded files
  are stored in the local project media directory in the development setup.
- Docker runs CPU-only PyTorch. The first embedding request can be slow while
  the model loads; hosted generation adds network/provider latency.
- Long PDFs are sampled at the beginning and end, so information only in the
  middle may be missed. PDF image/scanned-text OCR is not implemented.
- OCR is dependent on Tesseract and currently requests English.
- Image OCR exists as an extractor but image file types are not in the current
  asynchronous analysis allowlist, so image AI analysis is not wired end to end.
- The upload route extracts text once synchronously for category placement and
  again in the queued analysis task.
- Retrieval has a fixed top-five and 0.35 similarity threshold. Their optimal
  values have not been established by a valid, human-judged evaluation.
- Citations are parsed from bracketed numbers in model text; malformed or
  incorrect citations are possible.
- The generator is a remote dependency. A model being accepted in a smoke test
  does not guarantee every prompt will return a usable text block.
- The current evaluation corpus and metrics are too small/weak to substantiate
  production search-quality claims.
- The Compose file uses Django's development server and development-oriented
  database credentials. Do not expose this setup as a public production
  service. Production would require hardened settings, a production WSGI/ASGI
  server, secure secrets, HTTPS, persistent object storage/backups, upload
  validation/scanning, rate limiting, and operational monitoring.
- Demo-seeding utilities are for local demonstration only; inspect and reset
  their account/data before using the app in any shared environment.

These are appropriate scope boundaries for a portfolio project. State them
directly, then explain which one you would address first and why.

## 8. Suggested live demonstration

Use synthetic or explicitly non-sensitive documents and a clean demo account.

1. Show the vault, folder hierarchy, dashboard, and file operations.
2. Upload a small text-based PDF or TXT with clear content.
3. Explain that upload is saved first and analysis runs asynchronously.
4. Show the analysis status, then the generated summary, tags, and suggested
   folder after the worker finishes.
5. Ask a question whose answer appears in the uploaded document; show the
   cited source.
6. Ask an unrelated question and explain that RAG should report when the
   document context does not contain an answer.
7. Describe the data path: extracted text -> overlapping chunks -> local
   embeddings -> pgvector retrieval -> prompt with excerpts -> generated answer.

Avoid promising a fixed response time: local model warm-up and network/model
latency vary. For a live demo, run `ai_smoke_test` and ensure the worker is
running before presenting.

## 9. Likely defense questions

**Why use an LLM at all?**  
The LLM turns extracted text into readable summaries and tags and synthesizes
answers across retrieved passages. File CRUD and authorization remain
deterministic application code.

**How do you stop one user seeing another user's documents?**  
The authenticated user is used to scope file access and vector retrieval. The
RAG query filters chunks through their owning file and excludes trashed files.
The model only receives the filtered excerpts. This is an important invariant
to keep covered by tests as sharing behavior evolves.

**How do you reduce hallucination?**  
Retrieve relevant passages, include those passages in the prompt, instruct the
model to answer from them and cite them, and state when evidence is missing.
This reduces risk but is not a formal guarantee; citations and answers still
need evaluation.

**Why overlap chunks?**  
The overlap retains a small amount of boundary context so a fact split between
adjacent chunks is less likely to become unretrievable. It modestly increases
storage and duplicate retrieval.

**Why choose 384-dimensional embeddings?**  
That is the output dimension of the selected compact sentence-transformers
model. It reduces vector storage and is adequate for a prototype; quality
should be compared against alternatives using a labeled benchmark.

**Why put vectors in PostgreSQL?**  
It reuses the relational database and supports SQL ownership filters with vector
distance ordering, reducing service count and synchronization complexity.

**What happens when AI is unavailable?**  
Upload and extraction status are tracked separately from the generated answer.
Generation can use a configured fallback for provider/client failures, and
endpoints return explicit failures for some unavailable paths. An empty
successful response can still fail a request; provider metadata and timings
are logged to diagnose it.

**What is the main bottleneck?**  
It depends on the stage. First-time embedding-model load and local CPU
embedding affect retrieval; the hosted generation API contributes variable
network and model latency. The app records retrieval/generation timing so those
costs can be distinguished.

**What would you improve next?**  
First, build a reliable, human-judged retrieval benchmark and use it to tune
chunking, top-K, and the threshold. Then add robust API retries/timeouts and
streaming, move extraction fully out of the upload request, improve PDF OCR
coverage, and harden deployment/security before serving real users.

## 10. Five points to remember

1. Describe it as a **Django personal vault prototype with AI features**, not a
   production cloud-drive service.
2. Embeddings and generation are different: embeddings run locally; generation
   uses a configurable external model API.
3. RAG retrieves passages from the user's own stored documents and sends those
   excerpts to the model; it does not fine-tune the model.
4. Explain the trade-offs and limits—especially the invalid current benchmark,
   sampled long PDFs, CPU inference, and development deployment.
5. Demonstrate one complete upload-to-cited-answer flow and keep the discussion
   anchored to code paths and tests.
