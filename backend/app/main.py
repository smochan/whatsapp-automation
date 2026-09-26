from fastapi import FastAPI

from app.api.routes.whatsapp import router as whatsapp_router

app = FastAPI(
    title="WhatsApp Automation API",
    version="0.1.0",
    description="Backend for the standalone WhatsApp automation platform.",
)

app.include_router(whatsapp_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
