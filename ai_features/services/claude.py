import json
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


def _build_client(api_key: str, base_url: str):
    """
    Builds an Anthropic-compatible client. Empty base_url means api.anthropic.com.
    """
    if not api_key:
        return None
    try:
        import anthropic
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return anthropic.Anthropic(**kwargs)
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        return None


def get_anthropic_client():
    """
    Primary generation client. Supports custom base_url endpoints
    (e.g. AgentRouter/OneAPI proxies) via ANTHROPIC_BASE_URL.
    """
    return _build_client(
        getattr(settings, "ANTHROPIC_API_KEY", ""),
        getattr(settings, "ANTHROPIC_BASE_URL", ""),
    )


def get_fallback_client():
    """
    Secondary generation client, used only when the primary path is unavailable
    or errors. Also an Anthropic-compatible endpoint — the gateway exposes
    non-Claude models (e.g. gpt-5.6-sol) through /v1/messages.
    Returns None unless AI_FALLBACK_MODEL is configured.
    """
    if not getattr(settings, "AI_FALLBACK_MODEL", ""):
        return None
    return _build_client(
        getattr(settings, "AI_FALLBACK_API_KEY", ""),
        getattr(settings, "AI_FALLBACK_BASE_URL", ""),
    )



def _extract_text(response) -> str:
    """
    Joins the text blocks of a messages response, ignoring any non-text blocks.
    """
    if not getattr(response, "content", None):
        return ""
    return "".join(getattr(block, "text", "") for block in response.content)


def clean_json_string(raw: str) -> str:
    """
    Extracts JSON substring from raw model output (handles ```json code blocks).
    """
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def generate_text(system_prompt: str, user_content: str, max_tokens: int = 1000) -> str:
    """
    Single-turn completion via the primary Anthropic-compatible endpoint,
    falling back to AI_FALLBACK_MODEL if the primary client is unavailable
    or the call fails. Returns "" if both fail.
    """
    client = get_anthropic_client()
    if client:
        model = getattr(settings, "AI_CLAUDE_MODEL", "claude-opus-5")
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            return _extract_text(response)
        except Exception as e:
            logger.error(f"Primary generation call failed ({model}): {e}")
    else:
        logger.warning("Anthropic client unavailable; trying fallback model.")

    return _generate_text_fallback(system_prompt, user_content, max_tokens)


def _generate_text_fallback(system_prompt: str, user_content: str, max_tokens: int = 1000) -> str:
    """
    Generation via the secondary model. No-op unless AI_FALLBACK_MODEL is set.
    """
    model = getattr(settings, "AI_FALLBACK_MODEL", "")
    if not model:
        return ""

    client = get_fallback_client()
    if not client:
        logger.warning("Fallback model configured but its client is unavailable (missing key?).")
        return ""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        return _extract_text(response)
    except Exception as e:
        logger.error(f"Fallback generation call failed ({model}): {e}")
        return ""


def generate_json(system_prompt: str, user_content: str, schema_description: str = "") -> dict:
    """
    Queries the configured generation model and returns parsed JSON.
    Includes 1 retry attempt on JSON parse failure.
    """
    full_system = f"{system_prompt}\nRespond strictly with valid JSON. No conversational text."
    if schema_description:
        full_system += f"\nExpected JSON Schema: {schema_description}"

    for attempt in range(2):
        raw_text = generate_text(full_system, user_content)
        if not raw_text:
            logger.error("Generation returned no text; cannot parse JSON.")
            return {}
        try:
            return json.loads(clean_json_string(raw_text))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")

    logger.error("Failed to parse JSON response after 2 attempts.")
    return {}
