import os
import json
import time
import requests
import logging
from typing import Optional
from dotenv import load_dotenv
from .tools.tools_mapping import tools_schemas_map, tools_functions_map

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, model: str, base_url: str, api_key: Optional[str] = None):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @property
    def cost_usd(self) -> float:
        input_price  = float(os.getenv("MODEL_INPUT_PRICE_PER_1M",  "0"))
        output_price = float(os.getenv("MODEL_OUTPUT_PRICE_PER_1M", "0"))
        return (self.total_prompt_tokens     / 1_000_000) * input_price \
             + (self.total_completion_tokens / 1_000_000) * output_price

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

                for attempt in range(1, 4):
                    response = requests.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=120,
                    )
                    if response.status_code < 500:
                        break
                    logger.warning(f"Server error {response.status_code}, retry {attempt}/3 in {attempt * 5}s...")
                    time.sleep(attempt * 5)
                response.raise_for_status()
                body = response.json()
                usage = body.get("usage", {})
                self.total_prompt_tokens     += usage.get("prompt_tokens", 0)
                self.total_completion_tokens += usage.get("completion_tokens", 0)
                message = body["choices"][0]["message"]

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