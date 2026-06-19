import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if not api_key:
            raise RuntimeError("Missing LLM_API_KEY in environment.")

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        if max_tokens is None:
            env_max_tokens = os.getenv("LLM_MAX_TOKENS")
            if env_max_tokens:
                max_tokens = int(env_max_tokens)

        if max_tokens is not None:
            request["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**request)
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt + "\n\n只输出合法 JSON，不要输出 Markdown，不要使用 ```json 代码块。",
                }
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        if max_tokens is None:
            env_max_tokens = os.getenv("LLM_MAX_TOKENS")
            if env_max_tokens:
                max_tokens = int(env_max_tokens)

        if max_tokens is not None:
            request["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**request)
        content = response.choices[0].message.content or ""

        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            raise ValueError(f"LLM did not return valid JSON: {content}") from error
