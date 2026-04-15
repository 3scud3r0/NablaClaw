from __future__ import annotations

from dataclasses import dataclass, field

from nablaclaw.channels.base import ChannelAdapter, ChannelMessage


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

    def broadcast(self, user_id: str, text: str, platforms: list[str] | None = None) -> list[str]:
        targets = platforms or list(self.adapters.keys())
        receipts: list[str] = []
        for platform in targets:
            receipts.append(self.send(platform=platform, user_id=user_id, text=text))
        return receipts
