import hashlib
import hmac
from typing import Any

import httpx

from app.core.config import get_settings


class WhatsAppAPIError(RuntimeError):
    pass


class WhatsAppClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.settings.whatsapp_api_version}"

    def verify_signature(self, body: bytes, signature_header: str | None) -> bool:
        secret = self.settings.meta_app_secret
        if not secret or not signature_header:
            return False
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    async def send_text(
        self,
        *,
        phone_number_id: str,
        recipient: str,
        text: str,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        token = access_token or self.settings.whatsapp_access_token
        if not token:
            raise WhatsAppAPIError("No WhatsApp access token is configured")

        url = f"{self.base_url}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.is_error:
            raise WhatsAppAPIError(f"WhatsApp API error {response.status_code}: {response.text}")
        return response.json()


def extract_text_message(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the first customer text message from a Cloud API webhook payload."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                return {
                    "phone_number_id": metadata.get("phone_number_id"),
                    "from": message.get("from"),
                    "message_id": message.get("id"),
                    "timestamp": message.get("timestamp"),
                    "text": message.get("text", {}).get("body", ""),
                    "raw": message,
                }
    return None
