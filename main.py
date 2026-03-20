import os
import logging
from datetime import datetime
from agent.invoke import Agent
from jobs.cleaner import clean_temp_files
from jobs.layout import apply_layout
from jobs.printer import print_paper
from jobs.scraper import scrape_news
logging.basicConfig(level=logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(CURRENT_DIR, "prompts")
TODAY = datetime.now().strftime("%A, %B %-d, %Y")


def _read_prompt(filename: str) -> str:
    with open(os.path.join(PROMPTS_DIR, filename), "r", encoding="utf-8") as f:
        return f.read().strip()


def _load_meta_prompt() -> str:
    newspaper_css      = _read_prompt("newspaper_css.md")
    section_system     = _read_prompt("section_system.md")
    html_system        = (
        _read_prompt("html_system.md")
        .replace("{NEWSPAPER_CSS}", newspaper_css)
        .replace("{TODAY}", TODAY)
    )
    return (
        _read_prompt("meta_prompt.md")
        .replace("{SECTION_SYSTEM_PROMPT}", section_system)
        .replace("{HTML_SYSTEM_PROMPT}", html_system)
    )

# Switch between architectures:
#   "streamline" - Python drives the workflow, model only writes text (reliable, works with small models)
#   "agent"      - Model drives the workflow via tool calls (experimental, needs a capable model)
MODE = "streamline"
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("OPENAI_API_KEY")
URL = os.getenv("OPENAI_BASE_URL")
agent = Agent(model=MODEL_NAME, base_url=URL, api_key=API_KEY)

if __name__ == "__main__":
    # Clean temp files
    clean_temp_files()

    # Scrape news
    scrape_news()
    # Run the workflow
    if MODE == "streamline":
        from pipeline.run import run
        run(agent)
    elif MODE == "agent":
        system_prompt = _load_meta_prompt()
        try:
            with open(os.path.join(CURRENT_DIR, "user_preferences.md"), "r", encoding="utf-8") as f:
                user_preferences = f.read().strip()
        except FileNotFoundError:
            user_preferences = ""
        if user_preferences:
            system_prompt += f"\n\nUser preferences:\n{user_preferences}"
        response = agent.invoke("Prepare the paper.", system_prompt, tools=["run_agent", "check_file"])
        print(response)

        # Fallback: if the agent returned HTML directly instead of saving it via run_agent, save it now
        html_path = os.path.join(CURRENT_DIR, "temp_storage", "paper_final.html")
        if not os.path.exists(html_path) and response and "<html" in response.lower():
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response)
            print(f"Saved HTML response to {html_path}")

        # Apply layout post-processing (two-column split + CSS refresh)
        if os.path.exists(html_path) and os.path.getsize(html_path) > 0:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            html = apply_layout(html, TODAY, agent.cost_usd)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
    else:
        raise ValueError(f"Unknown MODE: '{MODE}'. Use 'streamline' or 'agent'.")

    # Print paper
    print_paper()