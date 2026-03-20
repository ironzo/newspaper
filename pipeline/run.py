import os
import logging
from datetime import datetime
from jobs.layout import apply_layout

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_NEWS_PATH      = os.path.join(ROOT_DIR, "temp_storage", "raw_news.md")
SUMMARIZED_PATH    = os.path.join(ROOT_DIR, "temp_storage", "summarized_paper.md")
HTML_PATH          = os.path.join(ROOT_DIR, "temp_storage", "paper_final.html")
USER_PREFS_PATH    = os.path.join(ROOT_DIR, "user_preferences.md")
PROMPTS_DIR        = os.path.join(ROOT_DIR, "prompts")

TODAY = datetime.now().strftime("%A, %B %-d, %Y")  # e.g. Friday, March 20, 2026

SECTIONS = [
    {"title": "Політика та гарячі новини", "prompt_file": "section_politics.md"},
    {"title": "Будапешт",                  "prompt_file": "section_budapest.md"},
    {"title": "Економіка",                 "prompt_file": "section_economics.md"},
    {"title": "Фінанси",                   "prompt_file": "section_finance.md"},
    {"title": "Технології та ШІ",          "prompt_file": "section_tech.md"},
    {"title": "Інше",                      "prompt_file": "section_other.md"},
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


def run(agent) -> None:
    user_prefs = _load_user_preferences()

    section_system_prompt = _read_prompt("section_system.md") + user_prefs
    html_system_prompt = _compose_html_system_prompt(user_prefs)

    with open(RAW_NEWS_PATH, "r", encoding="utf-8") as f:
        raw_news = f.read()

    open(SUMMARIZED_PATH, "w", encoding="utf-8").close()

    for section in SECTIONS:
        logger.info(f"Writing section: {section['title']}")
        section_prompt = _read_prompt(section["prompt_file"])
        prompt = f"{section_prompt}\n\n---СИРІ НОВИНИ---\n{raw_news}"
        content = agent.invoke(prompt, section_system_prompt)

        with open(SUMMARIZED_PATH, "a", encoding="utf-8") as f:
            f.write(f"## {section['title']}\n\n{content}\n\n")

        logger.info(f"Section '{section['title']}' written.")

    logger.info("Deduplicating sections...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        draft = f.read()
    dedup_prompt = _read_prompt("dedup.md")
    deduped = agent.invoke(f"{dedup_prompt}\n\n---ЧЕРНЕТКА---\n{draft}", section_system_prompt)
    with open(SUMMARIZED_PATH, "w", encoding="utf-8") as f:
        f.write(deduped)
    logger.info("Deduplication done.")

    logger.info("Generating HTML...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        summarized = f.read()

    html = agent.invoke(
        f"Перетвори цю газету на HTML згідно з інструкціями в системному промпті:\n\n{summarized}",
        html_system_prompt,
    )

    html = apply_layout(html, TODAY, agent.cost_usd)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Done. HTML saved to {HTML_PATH}")
