import os
import logging
from agent.invoke import Agent

logging.basicConfig(level=logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Switch between architectures:
#   "streamline" - Python drives the workflow, model only writes text (reliable, works with small models)
#   "agent"      - Model drives the workflow via tool calls (experimental, needs a capable model)
MODE = "streamline"

agent = Agent()

if __name__ == "__main__":
    if MODE == "streamline":
        from pipeline.run import run
        run(agent)
    elif MODE == "agent":
        with open(os.path.join(CURRENT_DIR, "user_preferences.md"), "r", encoding="utf-8") as f:
            system_prompt = f.read()
        response = agent.invoke("Prepare the paper.", system_prompt, tools=["execute_agent", "check_file"])
        print(response)
    else:
        raise ValueError(f"Unknown MODE: '{MODE}'. Use 'streamline' or 'agent'.")
