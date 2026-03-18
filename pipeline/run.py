import os
import logging

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_NEWS_PATH = os.path.join(ROOT_DIR, "temp_storage", "raw_news.md")
SUMMARIZED_PATH = os.path.join(ROOT_DIR, "temp_storage", "summarized_paper.md")
HTML_PATH = os.path.join(ROOT_DIR, "temp_storage", "prepared_paper.html")

SECTIONS = [
    {
        "title": "1. Politics and Hot News",
        "prompt": (
            "Write the 'Politics and Hot News' section of a morning newspaper. "
            "Include three subsections: 1.1 Ukraine, 1.2 USA and Europe, 1.3 Other World. "
            "Use only relevant news from the raw news below. Be factual, concise, cite sources. Max 300 words total."
        ),
    },
    {
        "title": "2. Economics News",
        "prompt": (
            "Write the 'Economics News' section of a morning newspaper. "
            "Use only relevant economics news from the raw news below. Be factual, concise, cite sources. Max 150 words."
        ),
    },
    {
        "title": "3. Financial News",
        "prompt": (
            "Write the 'Financial News' section of a morning newspaper. "
            "Use only relevant financial news from the raw news below. Be factual, concise, cite sources. Max 150 words."
        ),
    },
    {
        "title": "4. DataScience News",
        "prompt": (
            "Write the 'DataScience News' section of a morning newspaper. "
            "Include three subsections: 4.1 AI Engineering (fine-tuning, pipelines, tools), "
            "4.2 ML (training models, new architectures), 4.3 Other. "
            "Use only relevant news from the raw news below. Be factual, concise, cite sources. Max 300 words total."
        ),
    },
    {
        "title": "5. Other",
        "prompt": (
            "Write the 'Other' section of a morning newspaper with any remaining notable news "
            "not covered by politics, economics, finance, or data science. "
            "Use only relevant news from the raw news below. Be factual, concise. Max 100 words."
        ),
    },
]

SECTION_SYSTEM_PROMPT = (
    "You are a professional newspaper editor. You write clear, factual, well-structured newspaper articles. "
    "Write only the requested section. Do not add introductions, commentary, or markdown formatting beyond headers. "
    "If there is no relevant news for a section, write a single line: '[No relevant news today]'."
)

HTML_SYSTEM_PROMPT = (
    "You are a web designer specializing in print-ready HTML newspapers. "
    "Convert the provided markdown newspaper content into a complete, self-contained HTML file. "
    "Style it in an old-paper / vintage newspaper aesthetic: sepia tones, serif fonts, column layout, "
    "ornamental dividers between sections. The output must be a single valid HTML file with embedded CSS, "
    "ready to print on 2 A4 pages. Output only the raw HTML, no explanation."
)


def run(agent) -> None:
    with open(RAW_NEWS_PATH, "r", encoding="utf-8") as f:
        raw_news = f.read()

    open(SUMMARIZED_PATH, "w", encoding="utf-8").close()

    for section in SECTIONS:
        logger.info(f"Writing section: {section['title']}")
        prompt = f"{section['prompt']}\n\n---RAW NEWS---\n{raw_news}"
        content = agent.invoke(prompt, SECTION_SYSTEM_PROMPT)

        with open(SUMMARIZED_PATH, "a", encoding="utf-8") as f:
            f.write(f"## {section['title']}\n\n{content}\n\n")

        logger.info(f"Section '{section['title']}' written.")

    logger.info("Generating HTML...")
    with open(SUMMARIZED_PATH, "r", encoding="utf-8") as f:
        summarized = f.read()

    html = agent.invoke(
        f"Convert this newspaper to print-ready HTML:\n\n{summarized}",
        HTML_SYSTEM_PROMPT,
    )

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Done. HTML saved to {HTML_PATH}")
