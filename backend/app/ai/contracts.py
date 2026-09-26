from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class IntentResult:
    intent: str
    confidence: float
    language: str | None = None
    requires_human: bool = False


class Router(Protocol):
    async def classify(self, message: str, *, context: str = "") -> IntentResult:
        ...


class ResponseGenerator(Protocol):
    async def generate(self, *, user_message: str, context: str, instructions: str = "") -> str:
        ...
