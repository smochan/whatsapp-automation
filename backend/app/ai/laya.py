import httpx

from app.ai.contracts import IntentResult
from app.core.config import get_settings


class LayaRouter:
    """Thin adapter around a self-hosted Laya router.

    The product deliberately depends on this interface rather than a specific
    model/runtime package, so the deployment can run Laya locally or expose it
    over an internal HTTP endpoint without changing the WhatsApp layer.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def classify(self, message: str, *, context: str = "") -> IntentResult:
        if not self.settings.laya_base_url:
            raise RuntimeError("LAYA_BASE_URL is not configured")

        payload = {
            "task": "intent_classification",
            "message": message,
            "context": context,
            "output_schema": {
                "intent": "string",
                "confidence": "number",
                "language": "string|null",
                "requires_human": "boolean",
            },
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.laya_api_key:
            headers["Authorization"] = f"Bearer {self.settings.laya_api_key}"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self.settings.laya_base_url.rstrip('/')}/classify",
                json=payload,
                headers=headers,
            )
        response.raise_for_status()
        data = response.json()
        return IntentResult(
            intent=str(data["intent"]),
            confidence=float(data.get("confidence", 0.0)),
            language=data.get("language"),
            requires_human=bool(data.get("requires_human", False)),
        )
