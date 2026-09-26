import httpx

from app.ai.contracts import ResponseGenerator
from app.core.config import get_settings


class OpenAICompatibleGenerator(ResponseGenerator):
    """Small adapter for any OpenAI-compatible chat-completions endpoint."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(self, *, user_message: str, context: str, instructions: str = "") -> str:
        if not self.settings.llm_base_url or not self.settings.llm_api_key or not self.settings.llm_model:
            raise RuntimeError("LLM_BASE_URL, LLM_API_KEY and LLM_MODEL are required")

        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": instructions or "Answer using only the supplied business context. If the context is insufficient, say so and ask for the missing information."},
                {"role": "system", "content": f"Business context:\n{context}"},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
