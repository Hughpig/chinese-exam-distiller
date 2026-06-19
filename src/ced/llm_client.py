import os

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
        request = {
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
