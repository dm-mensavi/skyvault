import logging

from vault.models import File
from .models import FileAnalysis
from .extractors import extract_text
from .services.claude import generate_json

logger = logging.getLogger(__name__)

# Truncate extracted text before sending to Claude to stay within token limits (Phase 1).
MAX_TEXT_CHARS = 8000

ANALYSIS_SYSTEM_PROMPT = (
    "You analyze documents for a personal file vault. Return ONLY valid JSON with this schema:\n"
    "{\n"
    '  "summary": "2-3 sentence summary",\n'
    '  "tags": ["tag1", "tag2", ...],        // 3-7 lowercase tags\n'
    '  "suggested_folder": "folder name"     // e.g. "Taxes", "Work", "Personal"\n'
    "}\n"
    "No markdown fences. No extra keys."
)

ANALYSIS_SCHEMA = '{"summary": str, "tags": list[str], "suggested_folder": str}'


def analyze_file(file_id: int):
    """
    Background task: extract text from an uploaded file, ask Claude for a
    structured summary + tags + suggested folder, and persist the result.

    Status lifecycle: PENDING -> PROCESSING -> DONE | SKIPPED | FAILED.
    Failures never raise past this function so the upload itself is unaffected.
    """
    analysis = None
    try:
        file_obj = File.objects.get(id=file_id)
        logger.info(f"analyze_file starting for file_id={file_id} ({file_obj.name})")

        analysis, _ = FileAnalysis.objects.get_or_create(
            file=file_obj,
            defaults={"status": FileAnalysis.Status.PENDING},
        )

        if analysis.status == FileAnalysis.Status.SKIPPED:
            logger.info(f"file_id={file_id} is an unsupported format, keeping SKIPPED.")
            return

        analysis.status = FileAnalysis.Status.PROCESSING
        analysis.save(update_fields=["status", "updated_at"])

        # 1. Extract text
        if not file_obj.uploaded_file:
            _mark_skipped(analysis, "No file on disk.")
            return

        extension = file_obj.uploaded_file.name.split(".")[-1].lower()
        text = extract_text(file_obj.uploaded_file.path, extension)

        if not text or not text.strip():
            logger.info(f"file_id={file_id}: no extractable text, marking SKIPPED.")
            _mark_skipped(analysis, "No extractable text content.")
            return

        truncated = text[:MAX_TEXT_CHARS]

        # 2. Ask Claude for structured JSON
        result = generate_json(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_content=truncated,
            schema_description=ANALYSIS_SCHEMA,
        )

        if not result:
            raise ValueError("Claude returned an empty or invalid response.")

        # 3. Persist analysis results
        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        analysis.summary = str(result.get("summary", "")).strip()
        analysis.tags = [str(t).strip().lower() for t in tags if str(t).strip()]
        analysis.suggested_folder = str(result.get("suggested_folder", "")).strip()
        analysis.extracted_text = text  # full text stored for Phase 2 re-use
        analysis.error_message = ""
        analysis.status = FileAnalysis.Status.DONE
        analysis.save()

        # 4. Phase 2: Chunking & OpenAI Vector Embedding Indexing
        _index_vector_chunks(file_obj, analysis, text)

        logger.info(
            f"analyze_file done for file_id={file_id}: "
            f"{len(analysis.tags)} tags, {len(analysis.summary)} char summary."
        )

    except File.DoesNotExist:
        logger.warning(f"analyze_file: File with id={file_id} not found.")
    except Exception as e:
        logger.error(f"analyze_file error for file_id={file_id}: {e}", exc_info=True)
        _mark_failed(file_id, analysis, str(e))


def _index_vector_chunks(file_obj: File, analysis: FileAnalysis, text: str):
    """
    Chunks document text and generates OpenAI 1536-dimensional embeddings,
    saving DocumentChunk records for pgvector semantic search and RAG.
    """
    from .chunking import chunk_text
    from .services.embeddings import embed_texts
    from .models import DocumentChunk

    try:
        # Idempotently clear previous chunks
        DocumentChunk.objects.filter(file=file_obj).delete()

        chunks_data = chunk_text(text)
        if not chunks_data:
            logger.info(f"No chunks generated for file_id={file_obj.id}")
            return

        contents = [c["content"] for c in chunks_data]
        embeddings = embed_texts(contents)

        if not embeddings or len(embeddings) != len(chunks_data):
            logger.warning(f"Embedding count mismatch or failed for file_id={file_obj.id}")
            return

        new_chunks = [
            DocumentChunk(
                file=file_obj,
                analysis=analysis,
                chunk_index=c["chunk_index"],
                content=c["content"],
                embedding=embeddings[i],
                token_count=c["token_count"]
            )
            for i, c in enumerate(chunks_data)
        ]

        DocumentChunk.objects.bulk_create(new_chunks)
        logger.info(f"Successfully indexed {len(new_chunks)} vector chunks for file_id={file_obj.id}")
    except Exception as e:
        logger.error(f"Error indexing vector chunks for file_id={file_obj.id}: {e}", exc_info=True)



def _mark_skipped(analysis: FileAnalysis, reason: str):
    analysis.status = FileAnalysis.Status.SKIPPED
    analysis.error_message = reason
    analysis.save(update_fields=["status", "error_message", "updated_at"])


def _mark_failed(file_id: int, analysis: FileAnalysis | None, message: str):
    try:
        if analysis is None:
            analysis = FileAnalysis.objects.get(file_id=file_id)
        analysis.status = FileAnalysis.Status.FAILED
        analysis.error_message = message
        analysis.save(update_fields=["status", "error_message", "updated_at"])
    except Exception:
        logger.error(f"analyze_file: could not mark file_id={file_id} as FAILED.")
