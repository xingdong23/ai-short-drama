import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


SYSTEM_PROMPT = """
You write short serialized drama episodes for AI video generation.
Return JSON only. Do not wrap the result in markdown.
The JSON must contain:
- title: string
- theme: string
- scenes: list of objects with fields:
  - id: string
  - type: one of establishing, dialogue, action, transition
  - prompt: string
  - character: string or null
  - dialogue: string or null
  - duration: integer seconds
  - camera: string
Write 3 to 5 scenes with cinematic prompts suitable for image-to-video generation.
""".strip()


@dataclass(frozen=True)
class OpenAICompatibleLLMClient:
    api_base: str
    api_key: str
    model: str
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "OpenAICompatibleLLMClient | None":
        api_base = os.getenv("LLM_API_BASE")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_API_MODEL")
        timeout_raw = os.getenv("LLM_TIMEOUT_SECONDS", "60")

        if not api_base or not api_key or not model:
            return None

        return cls(
            api_base=api_base,
            api_key=api_key,
            model=model,
            timeout_seconds=int(timeout_raw),
        )

    def generate_script(self, theme: str) -> str:
        url = f"{self.api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Theme: {theme}\n"
                        "Generate one short-drama episode as strict JSON."
                    ),
                },
            ],
        }

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        response_payload = json.loads(response_body)
        content = self._extract_content(response_payload)
        if not content:
            raise ValueError("LLM response did not include text content")
        return content

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("LLM response missing choices")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            return "\n".join(parts)
        raise ValueError("Unsupported message content format")
