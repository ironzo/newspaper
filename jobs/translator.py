import os
import requests
import logging

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/lapa-llm/lapa-v0.1.2-instruct"

SECTION_TITLES_UK = {
    "Politics and Breaking News": "Політика та гарячі новини",
    "Budapest": "Будапешт",
    "Economics": "Економіка",
    "Finance": "Фінанси",
    "Technology and AI": "Технології та ШІ",
    "Other": "Інше",
    "[No news]": "[Новин немає]",
}


def translate_to_ukrainian(text: str) -> str:
    if not HF_TOKEN:
        raise EnvironmentError("HF_TOKEN is not set. Add it to .env to use LAPA translation.")

    prompt = (
        "Translate the following English newspaper text to Ukrainian. "
        "Preserve all formatting (markdown headers starting with ##, paragraph breaks). "
        "Do not add commentary or explanations — output only the translated text.\n\n"
        + text
    )

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json={"inputs": prompt, "parameters": {"max_new_tokens": 8192, "temperature": 0.2}},
        timeout=300,
    )
    resp.raise_for_status()
    result = resp.json()

    if isinstance(result, list) and result:
        translated = result[0].get("generated_text", "")
        # Strip the prompt prefix that some models echo back
        if translated.startswith(prompt):
            translated = translated[len(prompt):].strip()
        return translated

    raise ValueError(f"Unexpected LAPA API response: {result}")


def apply_title_fallback(text: str) -> str:
    """Replace any remaining English section headers with Ukrainian equivalents."""
    for en, uk in SECTION_TITLES_UK.items():
        text = text.replace(f"## {en}", f"## {uk}")
        text = text.replace(f"[No news]", "[Новин немає]")
    return text
