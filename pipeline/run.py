import os
import re
import json
import base64
import logging
from datetime import datetime
from jobs.archiver import load_recent_summaries
from jobs.layout import apply_layout
from jobs.image_selector import select_images
from agent.tools.weather_forecast import build_weather_html

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_NEWS_PATH      = os.path.join(ROOT_DIR, "temp_storage", "raw_news.md")
SUMMARIZED_PATH    = os.path.join(ROOT_DIR, "temp_storage", "summarized_paper.md")
HTML_PATH          = os.path.join(ROOT_DIR, "temp_storage", "paper_final.html")
USER_PREFS_PATH    = os.path.join(ROOT_DIR, "user_preferences.md")
PROMPTS_DIR        = os.path.join(ROOT_DIR, "prompts")
CITIES_PATH        = os.path.join(ROOT_DIR, "cities.md")

TODAY = datetime.now().strftime("%A, %B %-d, %Y")  # e.g. Friday, March 20, 2026

SECTIONS = [
    {"title": "Politics and Breaking News", "prompt_file": "section_politics.md"},
    {"title": "Budapest",                   "prompt_file": "section_budapest.md"},
    {"title": "Economics",                  "prompt_file": "section_economics.md"},
    {"title": "Finance",                    "prompt_file": "section_finance.md"},
    {"title": "Technology and AI",          "prompt_file": "section_tech.md"},
    {"title": "Other",                      "prompt_file": "section_other.md"},
]


def _read_prompt(filename: str) -> str:
    with open(os.path.join(PROMPTS_DIR, filename), "r", encoding="utf-8") as f:
        return f.read().strip()


def _compose_html_system_prompt(user_prefs: str) -> str:
    newspaper_css = _read_prompt("newspaper_css.md")
    return (
        _read_prompt("html_system.md")
        .replace("{NEWSPAPER_CSS}", newspaper_css)
        .replace("{TODAY}", TODAY)
        + user_prefs
    )


def _load_user_preferences() -> str:
    try:
        with open(USER_PREFS_PATH, "r", encoding="utf-8") as f:
            prefs = f.read().strip()
        return f"\n\nДодаткові побажання читача:\n{prefs}" if prefs else ""
    except FileNotFoundError:
        return ""


def _load_cities() -> list[str]:
    try:
        with open(CITIES_PATH, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def _split_into_items(raw_news: str) -> list[tuple[int, str, str | None]]:
    """Split raw news into numbered items (id, text, image_path). IMAGE tags are consumed."""
    IMAGE_TAG = re.compile(r'^\[IMAGE:\s*(.+?)\]\s*$')
    lines = raw_news.split('\n')
    items: list[tuple[int, str, str | None]] = []
    current_channel = ""
    current_item_lines: list[str] = []
    current_image: str | None = None
    item_id = 0

    def flush():
        nonlocal item_id, current_image
        text = '\n'.join(current_item_lines).strip()
        if text:
            items.append((item_id, f"{current_channel}\n{text}", current_image))
            item_id += 1
        current_image = None

    for line in lines:
        if line.startswith('## Channel Name:'):
            flush()
            current_item_lines = []
            current_channel = line
        elif line.startswith('### ['):
            flush()
            current_item_lines = [line]
        else:
            if current_item_lines:
                m = IMAGE_TAG.match(line)
                if m:
                    current_image = m.group(1).strip()
                else:
                    current_item_lines.append(line)

    flush()
    return items


def _route_news(
    agent, raw_news: str, section_titles: list[str]
) -> tuple[dict[str, str], list[tuple[int, str, str | None]], dict[str, list[int]]]:
    """Assign each raw news item to exactly one section.
    Returns (section_news, items, section_ids).
    """
    items = _split_into_items(raw_news)
    if not items:
        return {title: "" for title in section_titles}, items, {title: [] for title in section_titles}

    numbered = "\n\n".join(f"[{i}] {text}" for i, text, _ in items)
    router_prompt = _read_prompt("router.md")
    router_system = "You are a news router. Output valid JSON only, no markdown, no explanation."

    raw_result = agent.invoke(f"{router_prompt}\n\n---ITEMS---\n{numbered}", router_system)

    result = raw_result.strip()
    if result.startswith("```"):
        result = re.sub(r'^```[a-z]*\n?', '', result)
        result = re.sub(r'\n?```$', '', result)

    try:
        assignments = json.loads(result)
    except json.JSONDecodeError:
        logger.warning("Router returned invalid JSON — falling back to full news for all sections.")
        return {title: raw_news for title in section_titles}, items, {title: [] for title in section_titles}

    item_lookup = {i: (text, img) for i, text, img in items}
    seen_ids: set[int] = set()
    section_news: dict[str, str] = {}
    section_ids: dict[str, list[int]] = {}

    for title in section_titles:
        ids = assignments.get(title, [])
        unique_ids = [i for i in ids if i in item_lookup and i not in seen_ids]
        seen_ids.update(unique_ids)
        section_news[title] = "\n\n".join(item_lookup[i][0] for i in unique_ids)
        section_ids[title] = unique_ids

    return section_news, items, section_ids


def _inject_images(html: str, selected: list[dict]) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for img_info in selected:
        section_div = soup.find(attrs={"data-section": img_info["section"]})
        if not section_div:
            continue
        with open(img_info["image_path"], "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(img_info["image_path"])[1].lstrip(".") or "jpeg"
        caption = img_info["caption"].replace('"', '&quot;')
        figure_html = (
            f'<figure class="section-photo">'
            f'<img src="data:image/{ext};base64,{b64}" alt="{caption}"/>'
            f'<figcaption>{img_info["caption"]}</figcaption>'
            f'</figure>'
        )
        figure = BeautifulSoup(figure_html, "html.parser")
        section_div.insert(1, figure)
    return str(soup)


def run(agent) -> None:
    user_prefs = _load_user_preferences()

    archive_summaries = load_recent_summaries(n=3)
    archive_block = (
        "\n\n---PREVIOUS EDITIONS (for reference only)---\n"
        + archive_summaries
        + "\n---END OF PREVIOUS EDITIONS---\n"
    ) if archive_summaries else ""

    section_system_prompt = _read_prompt("section_system.md") + user_prefs + archive_block
    html_system_prompt = _compose_html_system_prompt(user_prefs)

    with open(RAW_NEWS_PATH, "r", encoding="utf-8") as f:
        raw_news = f.read()

    open(SUMMARIZED_PATH, "w", encoding="utf-8").close()

    logger.info("Routing news items to sections...")
    section_news, items, section_ids = _route_news(agent, raw_news, [s["title"] for s in SECTIONS])

    for section in SECTIONS:
        assigned = section_news.get(section["title"], "").strip()
        if not assigned:
            logger.info(f"Skipping section '{section['title']}' — no items assigned.")
            continue

        logger.info(f"Writing section: {section['title']}")
        section_prompt = _read_prompt(section["prompt_file"])
        prompt = f"{section_prompt}\n\n---RAW NEWS---\n{assigned}"
        content = agent.invoke(prompt, section_system_prompt)

        with open(SUMMARIZED_PATH, "a", encoding="utf-8") as f:
            f.write(f"## {section['title']}\n\n{content}\n\n")

        logger.info(f"Section '{section['title']}' written.")

    logger.info("Deduplicating sections...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        draft = f.read()
    dedup_prompt = _read_prompt("dedup.md")
    deduped = agent.invoke(f"{dedup_prompt}\n\n---DRAFT---\n{draft}", section_system_prompt)
    with open(SUMMARIZED_PATH, "w", encoding="utf-8") as f:
        f.write(deduped)
    logger.info("Deduplication done.")

    logger.info("Running final readability check...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        deduped = f.read()
    final_check_prompt = _read_prompt("final_check.md")
    polished = agent.invoke(f"{final_check_prompt}\n\n---DRAFT---\n{deduped}", section_system_prompt)
    with open(SUMMARIZED_PATH, "w", encoding="utf-8") as f:
        f.write(polished)
    logger.info("Readability check done.")

    logger.info("Translating paper to Ukrainian...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        english_draft = f.read()
    translation_system = (
        "You are a professional Ukrainian translator. "
        "Translate the provided English newspaper text to Ukrainian. "
        "Preserve all markdown formatting (## headings, paragraph breaks). "
        "Output only the translated text — no explanations, no commentary."
    )
    ukrainian_paper = agent.invoke(english_draft, translation_system)
    with open(SUMMARIZED_PATH, "w", encoding="utf-8") as f:
        f.write(ukrainian_paper)
    logger.info("Translation done.")

    logger.info("Generating HTML...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        summarized = f.read()

    html = agent.invoke(
        f"Перетвори цю газету на HTML згідно з інструкціями в системному промпті:\n\n{summarized}",
        html_system_prompt,
    )

    logger.info("Selecting images...")
    selected_images, vision_cost, vision_tokens = select_images(items, section_ids)
    if selected_images:
        logger.info(f"Injecting {len(selected_images)} image(s) into HTML.")
        html = _inject_images(html, selected_images)
    else:
        logger.info("No images selected.")

    total_tokens = agent.total_prompt_tokens + agent.total_completion_tokens + vision_tokens
    total_cost = agent.cost_usd + vision_cost
    html = apply_layout(html, TODAY, total_cost, total_tokens)

    logger.info("Fetching weather forecast...")
    cities = _load_cities()
    if cities:
        weather_html = build_weather_html(cities)
        if weather_html:
            html = re.sub(
                r'(<footer\s+class="footer">)',
                weather_html + r'\1',
                html,
                count=1,
            )
            logger.info("Weather forecast injected.")
        else:
            logger.warning("Weather forecast returned empty — skipping.")
    else:
        logger.warning("No cities found in cities.md — skipping weather forecast.")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Done. HTML saved to {HTML_PATH}")
    logger.info(f"Total cost: ${total_cost:.4f} ({total_tokens:,} tokens)")
