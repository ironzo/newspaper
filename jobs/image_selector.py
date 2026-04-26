import os
import base64
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

IMPORTANT_SECTIONS = {
    "Politics and Breaking News",
    "Budapest",
    "Economics",
    "Technology and AI",
}


def _call_vision(image_path: str, model: str, api_key: str, base_url: str) -> tuple[dict, dict]:
    """Returns (parsed_result, usage) where usage has prompt_tokens and completion_tokens."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(image_path)[1].lstrip(".") or "jpeg"
    mime = f"image/{ext}"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "This image is from a news article. "
                            "Reply with JSON only, no explanation: "
                            "{\"caption\": \"one-sentence newspaper caption\", \"score\": N} "
                            "where score is 1-5 (5 = major news event photo, "
                            "3 = relevant news, 1 = meme/promotional/irrelevant)."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 100,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    resp = requests.post(f"{base_url}/v1/chat/completions", json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    usage = body.get("usage", {})
    raw = body["choices"][0]["message"]["content"].strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    return json.loads(raw), usage


def select_images(
    items: list[tuple[int, str, str | None]],
    section_ids: dict[str, list[int]],
    n: int = 3,
) -> tuple[list[dict], float, int]:
    """Returns (selected, vision_cost_usd, vision_total_tokens).
    selected: up to n dicts {image_path, caption, section, score}, sorted by score desc.
    """
    model    = os.getenv("VISION_MODEL_NAME")
    api_key  = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    input_price  = float(os.getenv("VISION_INPUT_PRICE_PER_1M",  "0"))
    output_price = float(os.getenv("VISION_OUTPUT_PRICE_PER_1M", "0"))

    if not model:
        return [], 0.0, 0

    item_lookup = {i: (text, img) for i, text, img in items}

    candidates = []
    for section, ids in section_ids.items():
        if section not in IMPORTANT_SECTIONS:
            continue
        for item_id in ids:
            _, img = item_lookup.get(item_id, (None, None))
            if img and os.path.exists(img):
                candidates.append((item_id, img, section))

    results = []
    total_prompt_tokens = 0
    total_completion_tokens = 0

    for item_id, img, section in candidates:
        try:
            data, usage = _call_vision(img, model, api_key, base_url)
            total_prompt_tokens     += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            score = int(data.get("score", 0))
            caption = data.get("caption", "")
            if score >= 3 and caption:
                results.append({
                    "image_path": img,
                    "caption": caption,
                    "section": section,
                    "score": score,
                })
        except Exception as e:
            print(f"Vision call failed for {img}: {e}")

    vision_cost = (total_prompt_tokens / 1_000_000) * input_price \
                + (total_completion_tokens / 1_000_000) * output_price
    vision_tokens = total_prompt_tokens + total_completion_tokens

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:n], vision_cost, vision_tokens
