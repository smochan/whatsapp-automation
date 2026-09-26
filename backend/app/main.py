from fastapi import FastAPI

app = FastAPI(
    title="WhatsApp Automation API",
    version="0.1.0",
    description="Backend for the standalone WhatsApp automation platform.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
