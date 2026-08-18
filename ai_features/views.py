import json
import logging
import re
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ai_features.services.search import search_chunks, RetrievalUnavailable
from ai_features.services.claude import generate_text

logger = logging.getLogger(__name__)

# Common chitchat / greeting phrases that bypass RAG document search
CHITCHAT_PHRASES = {
    "hi", "hello", "hey", "heya", "greetings", "good morning", "good afternoon", "good evening",
    "how are you", "how are you doing", "whats up", "what's up", "who are you", "what are you",
    "what can you do", "who created you", "thanks", "thank you", "thx", "bye", "goodbye",
    "cool", "awesome", "great", "ok", "okay", "help"
}

RAG_SYSTEM_PROMPT = (
    "You are SkyVault AI, a friendly, intelligent personal cloud storage assistant.\n"
    "Guidelines:\n"
    "1. For questions about the user's files or document content: Answer using the provided document excerpts below and cite source files using bracket numbers, e.g. [1], [2].\n"
    "2. If the excerpts do not contain enough information to answer a document question, state clearly that you couldn't find relevant information in their uploaded documents."
)

GENERAL_SYSTEM_PROMPT = (
    "You are SkyVault AI, a friendly, intelligent personal cloud storage assistant.\n"
    "Respond warmly, naturally, and helpfully to the user's message (e.g. greetings, casual chat, general questions, or small talk).\n"
    "If the user asks about specific personal files or document contents that aren't available in their vault, politely let them know you couldn't find matching documents in SkyVault."
)


def is_chitchat_query(query: str) -> bool:
    """
    Detects if the user query is a casual greeting, small talk, or general chitchat phrase.
    """
    cleaned = re.sub(r'[^\w\s]', '', query.lower().strip())
    if cleaned in CHITCHAT_PHRASES:
        return True
    words = cleaned.split()
    if len(words) <= 3 and any(w in CHITCHAT_PHRASES for w in words):
        return True
    return False


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

    # 1. Check if the query is a casual greeting / chitchat phrase
    if is_chitchat_query(query):
        raw_chunks = []
    else:
        try:
            raw_chunks = search_chunks(request.user, query, top_k=5)
        except RetrievalUnavailable as e:
            logger.error(f"Semantic retrieval unavailable for ask_vault: {e}")
            return JsonResponse({
                "error": (
                    "Document search is currently unavailable, so I can't look through your "
                    "files. This usually means the embedding model failed to load. "
                    "Run 'python manage.py ai_smoke_test' to diagnose."
                ),
                "retrieval_unavailable": True,
            }, status=503)

    # Filter retrieved chunks by relevance score threshold (minimum 0.35 similarity).
    RELEVANCE_THRESHOLD = 0.35
    chunks = [c for c in raw_chunks if getattr(c, "relevance_score", 0) >= RELEVANCE_THRESHOLD]

    sources = []
    seen_files = set()

    if chunks:
        context_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            context_blocks.append(f"[{idx}] File: {chunk.file.name}\n{chunk.content}")
            if chunk.file_id not in seen_files:
                seen_files.add(chunk.file_id)
                sources.append({
                    "index": idx,
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
        # Use concise token limits for fast responses. RAG: 200 tokens, chitchat: 100.
        token_limit = 200 if chunks else 100
        answer = generate_text(system_prompt, user_prompt, max_tokens=token_limit)
        if not answer:
            if sources:
                return JsonResponse({
                    "answer": f"Found {len(sources)} relevant document(s), but no AI generation model is configured to synthesize an answer. Please set ANTHROPIC_AUTH_TOKEN in your environment.",
                    "sources": sources
                })
            else:
                return JsonResponse({
                    "answer": "Hello! I'm SkyVault AI, your personal cloud assistant. How can I help you with your files today?",
                    "sources": []
                })


        # Strict Citation Filter: Only include sources that were ACTUALLY cited in the AI answer text (e.g. [1], [2]).
        cited_indices = set(int(m) for m in re.findall(r'\[(\d+)\]', answer))
        final_sources = [s for s in sources if s.get("index") in cited_indices]

        return JsonResponse({
            "answer": answer,
            "sources": final_sources
        })
    except Exception as e:
        logger.error(f"Error in ask_vault RAG call: {e}", exc_info=True)
        return JsonResponse({
            "answer": "An error occurred while generating the answer. Please try again.",
            "sources": [],
            "error": "An error occurred while generating the answer. Please try again.",
        }, status=500)
