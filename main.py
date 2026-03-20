import os
import logging
from agent.invoke import Agent
from jobs.cleaner import clean_temp_files
from jobs.printer import print_paper
from jobs.scraper import scrape_news
logging.basicConfig(level=logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Switch between architectures:
#   "streamline" - Python drives the workflow, model only writes text (reliable, works with small models)
#   "agent"      - Model drives the workflow via tool calls (experimental, needs a capable model)
MODE = "agent"
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("OPENAI_API_KEY")
URL = os.getenv("OPENAI_BASE_URL")
agent = Agent(model=MODEL_NAME, base_url=URL, api_key=API_KEY)

if __name__ == "__main__":
    # Clean temp files
    clean_temp_files()

    # Scrape news
    scrape_news()

    # Print paper
    print_paper()

    # Run the workflow
    if MODE == "streamline":
        from pipeline.run import run
        run(agent)
    elif MODE == "agent":
        with open(os.path.join(CURRENT_DIR, "meta_prompt.md"), "r", encoding="utf-8") as f:
            system_prompt = f.read()
        with open(os.path.join(CURRENT_DIR, "user_preferences.md"), "r", encoding="utf-8") as f:
            user_preferences = f.read()
        if user_preferences:
            user_preferences = f"User preferences:\n{user_preferences}"
        else:
            user_preferences = ""
        sys_prompt = f"{system_prompt}\n\n{user_preferences}"
        response = agent.invoke("Prepare the paper.", system_prompt, tools=["run_agent", "check_file"])
        print(response)
    else:
        raise ValueError(f"Unknown MODE: '{MODE}'. Use 'streamline' or 'agent'.")
