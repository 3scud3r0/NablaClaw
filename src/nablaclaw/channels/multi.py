from __future__ import annotations

import time
from dataclasses import dataclass, field

from nablaclaw.channels.base import ChannelAdapter, ChannelMessage


@dataclass
class DeliveryResult:
    platform: str
    ok: bool
    receipt: str = ""
    error: str = ""


@dataclass
class ChannelHub:
    """Hub multi-canal para unificar comunicação com o usuário."""

    adapters: dict[str, ChannelAdapter] = field(default_factory=dict)

    def register(self, adapter: ChannelAdapter) -> None:
        self.adapters[adapter.platform] = adapter

    def send(self, platform: str, user_id: str, text: str) -> str:
        if platform not in self.adapters:
            raise KeyError(f"Canal '{platform}' não configurado")
        message = ChannelMessage(platform=platform, user_id=user_id, text=text)
        return self.adapters[platform].send(message)

    def send_with_retry(
        self,
        platform: str,
        user_id: str,
        text: str,
        retries: int = 2,
        backoff_seconds: float = 0.4,
    ) -> DeliveryResult:
        attempt = 0
        while attempt <= retries:
            try:
                receipt = self.send(platform=platform, user_id=user_id, text=text)
                return DeliveryResult(platform=platform, ok=True, receipt=receipt)
            except Exception as err:
                if attempt >= retries:
                    return DeliveryResult(platform=platform, ok=False, error=str(err))
                time.sleep(backoff_seconds * (2**attempt))
                attempt += 1
        return DeliveryResult(platform=platform, ok=False, error="unknown")

    def broadcast(
        self,
        user_id: str,
        text: str,
        platforms: list[str] | None = None,
        retries: int = 1,
    ) -> list[DeliveryResult]:
        targets = platforms or list(self.adapters.keys())
        results: list[DeliveryResult] = []
        for platform in targets:
            results.append(
                self.send_with_retry(platform=platform, user_id=user_id, text=text, retries=retries)
            )
        return results
