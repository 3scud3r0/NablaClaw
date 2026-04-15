from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib import request

from nablaclaw.adapters.base import ModelAdapter


def _http_post_json(
    *,
    url: str,
    payload: dict[str, object],
    headers: dict[str, str],
    timeout_seconds: int,
    retries: int,
) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = request.Request(
                url=url,
                method="POST",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            with request.urlopen(req, timeout=timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:
            last_error = err
            if attempt < retries:
                time.sleep(0.5 * (2**attempt))
    raise RuntimeError(f"Falha HTTP após retries: {last_error}")


@dataclass
class OllamaAdapter(ModelAdapter):
    """Adapter HTTP para Ollama local."""

    model: str
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: int = 30
    retries: int = 1

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        data = _http_post_json(
            url=f"{self.base_url}/api/generate",
            payload=payload,
            headers={"Content-Type": "application/json"},
            timeout_seconds=self.timeout_seconds,
            retries=self.retries,
        )
        return str(data.get("response", ""))


@dataclass
class OpenRouterAdapter(ModelAdapter):
    """Adapter HTTP para OpenRouter."""

    model: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: int = 30
    retries: int = 1

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = _http_post_json(
            url=f"{self.base_url}/chat/completions",
            payload={"model": self.model, "messages": messages},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout_seconds=self.timeout_seconds,
            retries=self.retries,
        )

        choices = data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", ""))
