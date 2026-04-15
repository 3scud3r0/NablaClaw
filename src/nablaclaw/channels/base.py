from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ChannelMessage:
    platform: str
    user_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class ChannelAdapter(ABC):
    """Contrato para canais externos (WhatsApp/Telegram/Discord/etc)."""

    platform: str

    @abstractmethod
    def send(self, message: ChannelMessage) -> str:
        raise NotImplementedError


class InMemoryChannelAdapter(ChannelAdapter):
    """Adapter para desenvolvimento e testes locais."""

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.outbox: list[ChannelMessage] = []

    def send(self, message: ChannelMessage) -> str:
        self.outbox.append(message)
        return f"{self.platform}:{len(self.outbox)}"
