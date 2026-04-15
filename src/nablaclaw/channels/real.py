from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request

from nablaclaw.channels.base import ChannelAdapter, ChannelMessage


@dataclass
class WebhookChannelAdapter(ChannelAdapter):
    """Adapter base para canais HTTP (Discord, Telegram, Twilio)."""

    platform: str = "custom"
    endpoint: str = ""
    auth_header: str | None = None
    timeout_seconds: int = 20

    def _payload(self, message: ChannelMessage) -> dict[str, str]:
        return {"text": message.text, "user_id": message.user_id}

    def send(self, message: ChannelMessage) -> str:
        payload = self._payload(message)
        headers = {"Content-Type": "application/json"}
        if self.auth_header:
            headers["Authorization"] = self.auth_header
        req = request.Request(
            url=self.endpoint,
            method="POST",
            headers=headers,
            data=json.dumps(payload).encode("utf-8"),
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            _ = resp.read()
        return f"{self.platform}:sent"


@dataclass
class DiscordWebhookAdapter(WebhookChannelAdapter):
    platform: str = "discord"

    def _payload(self, message: ChannelMessage) -> dict[str, str]:
        return {"content": f"[{message.user_id}] {message.text}"}


@dataclass
class TelegramBotAdapter(WebhookChannelAdapter):
    platform: str = "telegram"
    chat_id: str = ""

    def _payload(self, message: ChannelMessage) -> dict[str, str]:
        cid = self.chat_id or message.user_id
        return {"chat_id": cid, "text": message.text}


@dataclass
class TwilioWhatsAppAdapter(WebhookChannelAdapter):
    platform: str = "whatsapp"
    from_number: str = ""

    def _payload(self, message: ChannelMessage) -> dict[str, str]:
        return {
            "From": self.from_number,
            "To": message.user_id,
            "Body": message.text,
        }
