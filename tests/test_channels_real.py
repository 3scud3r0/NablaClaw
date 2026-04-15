from unittest.mock import MagicMock, patch

from nablaclaw.channels import ChannelMessage, DiscordWebhookAdapter, TelegramBotAdapter, TwilioWhatsAppAdapter


@patch("urllib.request.urlopen")
def test_discord_webhook_send(mock_urlopen: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"ok"
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    adapter = DiscordWebhookAdapter(endpoint="https://example.com/webhook")
    receipt = adapter.send(ChannelMessage(platform="discord", user_id="u1", text="olá"))
    assert receipt == "discord:sent"


def test_telegram_payload_format() -> None:
    adapter = TelegramBotAdapter(endpoint="https://api.telegram.org", chat_id="123")
    payload = adapter._payload(ChannelMessage(platform="telegram", user_id="u1", text="oi"))
    assert payload["chat_id"] == "123"


def test_twilio_payload_format() -> None:
    adapter = TwilioWhatsAppAdapter(endpoint="https://api.twilio.com", from_number="whatsapp:+111")
    payload = adapter._payload(ChannelMessage(platform="whatsapp", user_id="whatsapp:+222", text="hello"))
    assert payload["To"] == "whatsapp:+222"
    assert payload["From"] == "whatsapp:+111"
