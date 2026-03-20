import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))

run_agent_tool = {
    "type": "function",
    "function": {
        "name": "run_agent",
        "description": "Calls an agent, which uses tools to create a draft or summary of a topic, or generates a final version of a paper or generates a paper HTML with CSS style version.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": { "type": "string", "description": "Prompt for the agent." },
                "system_prompt": { "type": "string", "description": "System prompt for the agent." },
                "save_to": { "type": "string", "description": "Path relative to project root where the result will be saved (e.g. 'temp_storage/summarized_paper.md')." },
                "tools": { "type": "array", "items": { "type": "string" } },
                "force_tool": { "type": "string" }
            },
            "required": ["prompt", "system_prompt", "save_to"]
        }
    }
}

def run_agent(prompt: str, system_prompt: str = "", save_to: str = None, tools: list[str] = ["check_file"], force_tool: str = None) -> str:
    print(f"Called agent with prompt: {prompt}, system_prompt: {system_prompt}, tools: {tools}, force_tool: {force_tool}")
    from main import agent
    response = agent.invoke(prompt, system_prompt, tools, force_tool)
    if save_to:
        save_to = save_to.lstrip("/")
        path = os.path.join(ROOT_DIR, save_to)
        with open(path, "a", encoding="utf-8") as f:
            f.write(response + "\n")
        return f"The response is saved to {save_to}"
    return response
