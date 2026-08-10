import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ai_features.services.search import search_chunks
from ai_features.services.claude import generate_text

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = (
    "You are SkyVault AI, an intelligent personal file assistant.\n"
    "Answer the user's question using ONLY the provided document excerpts below.\n"
    "Rules:\n"
    "1. Cite source files using bracket numbers, e.g. [1], [2].\n"
    "2. Be concise, direct, and helpful (2-4 paragraphs max).\n"
    "3. If the excerpts do not contain enough information to answer, state clearly: "
    "'I couldn't find relevant documents in your SkyVault to answer this question.'"
)

GENERAL_SYSTEM_PROMPT = (
    "You are SkyVault AI, an intelligent personal file assistant.\n"
    "Answer the user's question directly, concisely, and helpfully (2-3 paragraphs max).\n"
    "If the user asks about specific personal files or documents that aren't available, mention that you couldn't find relevant documents in their SkyVault."
)


@login_required
@require_POST
def ask_vault(request):
    """
    RAG Q&A Endpoint: Retrieves relevant pgvector document chunks for user query,
    constructs context prompt, and generates grounded answer with source file citations.
    Falls back to direct AI generation for conversational queries when no chunks match.
    """
    query = ""
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
            query = data.get("query", "").strip()
        except Exception:
            pass
    if not query:
        query = request.POST.get("query", "").strip()

    if not query:
        return JsonResponse({"error": "Query cannot be empty."}, status=400)

    # 1. Retrieve top relevant chunks for current user
    chunks = search_chunks(request.user, query, top_k=5)

    sources = []
    seen_files = set()

    if chunks:
        context_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            context_blocks.append(f"[{idx}] File: {chunk.file.name}\n{chunk.content}")
            if chunk.file_id not in seen_files:
                seen_files.add(chunk.file_id)
                sources.append({
                    "id": chunk.file.id,
                    "name": chunk.file.name,
                    "score": chunk.relevance_score,
                })
        full_context = "\n\n---\n\n".join(context_blocks)
        user_prompt = f"Document Excerpts:\n{full_context}\n\nUser Question: {query}"
        system_prompt = RAG_SYSTEM_PROMPT
    else:
        user_prompt = query
        system_prompt = GENERAL_SYSTEM_PROMPT

    # 2. Synthesize the answer (primary model, with fallback)
    try:
        answer = generate_text(system_prompt, user_prompt, max_tokens=1000)
        if not answer:
            if sources:
                return JsonResponse({
                    "answer": f"Found {len(sources)} relevant document(s), but no AI generation model is configured to synthesize an answer. Please set ANTHROPIC_AUTH_TOKEN in your environment.",
                    "sources": sources
                })
            else:
                return JsonResponse({
                    "answer": "I couldn't find relevant documents in your SkyVault for this query. (Note: No AI generation model is currently configured to synthesize a general answer).",
                    "sources": []
                })
        return JsonResponse({
            "answer": answer,
            "sources": sources
        })
    except Exception as e:
        logger.error(f"Error in ask_vault RAG call: {e}", exc_info=True)
        return JsonResponse({
            "answer": "An error occurred while generating the answer. Please try again.",
            "sources": sources,
            "error": str(e)
        }, status=500)
