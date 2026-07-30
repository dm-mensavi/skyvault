import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ai_features.services.search import search_chunks
from ai_features.services.claude import get_anthropic_client

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


@login_required
@require_POST
def ask_vault(request):
    """
    RAG Q&A Endpoint: Retrieves relevant pgvector document chunks for user query,
    constructs context prompt, and generates grounded answer with source file citations.
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

    if not chunks:
        return JsonResponse({
            "answer": "I couldn't find any relevant documents in your SkyVault to answer this question.",
            "sources": []
        })

    # 2. Build grounded context block with source numbers
    context_blocks = []
    sources = []
    seen_files = set()

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

    # 3. Call Claude for answer synthesis
    client = get_anthropic_client()
    if not client:
        # Fallback if API key missing
        return JsonResponse({
            "answer": f"Found {len(sources)} relevant document(s), but Claude API key is not configured to synthesize an answer.",
            "sources": sources
        })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=RAG_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        answer = response.content[0].text if response.content else "No response generated."
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
