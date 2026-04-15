from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request

from nablaclaw.adapters.base import ModelAdapter


@dataclass
class OllamaAdapter(ModelAdapter):
    """Adapter HTTP para Ollama local."""

    model: str
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: int = 30

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        req = request.Request(
            url=f"{self.base_url}/api/generate",
            method="POST",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return str(data.get("response", ""))


@dataclass
class OpenRouterAdapter(ModelAdapter):
    """Adapter HTTP para OpenRouter."""

    model: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_seconds: int = 30

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            method="POST",
            data=json.dumps({"model": self.model, "messages": messages}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        choices = data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", ""))
