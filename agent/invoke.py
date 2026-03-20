import json
import requests
import logging
from typing import Optional
from dotenv import load_dotenv
from .tools.tools_mapping import tools_schemas_map, tools_functions_map

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, model: str ,  base_url: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
    def invoke(self, prompt: str, system_prompt: str = "", tools: list[str] = [], force_tool: str = None) -> str:
        try:
            msgs = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            tools_list = [tools_schemas_map[t] for t in tools] if tools else []

            if self.api_key:
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            else:
                headers = {"Content-Type": "application/json"}

            while True:
                payload = {"model": self.model, "messages": msgs}
                if tools_list:
                    payload["tools"] = tools_list
                    if force_tool:
                        payload["tool_choice"] = {"type": "function", "function": {"name": force_tool}}

                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                message = response.json()["choices"][0]["message"]

                tool_calls = message.get("tool_calls")
                if not tool_calls:
                    return message.get("content", "")

                msgs.append(message)

                for tool_call in tool_calls:
                    fn_name = tool_call["function"]["name"]
                    fn_args = json.loads(tool_call["function"]["arguments"])
                    logger.info(f"Calling tool: {fn_name} with args: {fn_args}")

                    if fn_name not in tools_functions_map:
                        result = f"Unknown tool: {fn_name}"
                    else:
                        result = tools_functions_map[fn_name](**fn_args)

                    logger.info(f"Tool result: {result}")
                    msgs.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(result)
                    })

                force_tool = None

        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise e