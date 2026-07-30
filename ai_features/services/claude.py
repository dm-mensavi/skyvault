import json
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


def get_anthropic_client():
    """
    Returns an instance of Anthropic client if API key is configured.
    """
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {e}")
        return None


def clean_json_string(raw: str) -> str:
    """
    Extracts JSON substring from raw model output (handles ```json code blocks).
    """
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def generate_json(system_prompt: str, user_content: str, schema_description: str = "") -> dict:
    """
    Queries Anthropic Claude and returns parsed JSON.
    Includes 1 retry attempt on JSON parse failure.
    """
    client = get_anthropic_client()
    if not client:
        logger.warning("Anthropic API key missing or client unavailable. Returning empty dict.")
        return {}

    model = getattr(settings, "AI_CLAUDE_MODEL", "claude-sonnet-4-20250514")
    full_system = f"{system_prompt}\nRespond strictly with valid JSON. No conversational text."
    if schema_description:
        full_system += f"\nExpected JSON Schema: {schema_description}"

    for attempt in range(2):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                system=full_system,
                messages=[{"role": "user", "content": user_content}]
            )
            raw_text = response.content[0].text if response.content else ""
            cleaned = clean_json_string(raw_text)
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
            if attempt == 1:
                logger.error("Failed to parse JSON response from Claude after 2 attempts.")
                return {}
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return {}

    return {}
