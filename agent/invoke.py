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

MAX_ATTEMPTS = 3
RETRY_DELAYS = [10, 20, 30]


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

    def _post_with_retry(self, payload: dict, headers: dict) -> requests.Response:
        last_exc = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=360,
                    stream=True,
                )
                if response.status_code == 200:
                    return response
                wait = RETRY_DELAYS[attempt - 1]
                logger.warning(
                    f"HTTP {response.status_code} on attempt {attempt}/{MAX_ATTEMPTS} "
                    f"(body: {response.text[:300]}), retrying in {wait}s..."
                )
                time.sleep(wait)
            except requests.exceptions.ReadTimeout as e:
                last_exc = e
                wait = RETRY_DELAYS[attempt - 1]
                logger.warning(f"ReadTimeout on attempt {attempt}/{MAX_ATTEMPTS}, retrying in {wait}s...")
                if attempt < MAX_ATTEMPTS:
                    time.sleep(wait)
        if last_exc:
            raise last_exc
        response.raise_for_status()
        return response

    def _parse_stream(self, response: requests.Response) -> tuple[str, list, dict]:
        """Consume an SSE stream and return (content, tool_calls, usage)."""
        content_parts = []
        # tool_calls_acc: index -> accumulated tool call dict
        tool_calls_acc: dict[int, dict] = {}
        usage = {}

        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue

            if chunk.get("usage"):
                usage = chunk["usage"]

            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})

            if delta.get("content"):
                content_parts.append(delta["content"])

            for tc in delta.get("tool_calls", []):
                idx = tc["index"]
                if idx not in tool_calls_acc:
                    tool_calls_acc[idx] = {
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("function", {}).get("name", ""),
                            "arguments": tc.get("function", {}).get("arguments", ""),
                        },
                    }
                else:
                    if tc.get("id"):
                        tool_calls_acc[idx]["id"] = tc["id"]
                    fn = tc.get("function", {})
                    if fn.get("name"):
                        tool_calls_acc[idx]["function"]["name"] += fn["name"]
                    if fn.get("arguments"):
                        tool_calls_acc[idx]["function"]["arguments"] += fn["arguments"]

        content = "".join(content_parts)
        tool_calls = [tool_calls_acc[i] for i in sorted(tool_calls_acc)]
        return content, tool_calls, usage

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
                payload = {
                    "model": self.model,
                    "messages": msgs,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                }
                if tools_list:
                    payload["tools"] = tools_list
                    if force_tool:
                        payload["tool_choice"] = {"type": "function", "function": {"name": force_tool}}

                response = self._post_with_retry(payload, headers)
                content, tool_calls, usage = self._parse_stream(response)

                self.total_prompt_tokens     += usage.get("prompt_tokens", 0)
                self.total_completion_tokens += usage.get("completion_tokens", 0)

                if not tool_calls:
                    return content

                msgs.append({"role": "assistant", "content": content or None, "tool_calls": tool_calls})

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