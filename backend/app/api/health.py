from fastapi import APIRouter
import httpx
from app.config import settings

router = APIRouter(tags=["health"])

MOCK_KEY_PREFIXES = ("mock", "your-", "change", "sk-placeholder", "test-key", "replace")


def _is_mock_key() -> bool:
    key = (settings.openai_api_key or "").lower()
    return not key or any(key.startswith(p) for p in MOCK_KEY_PREFIXES)


async def _check_ollama_health() -> dict:
    is_ollama = (
        "ollama" in (settings.openai_base_url or "").lower()
        or (settings.openai_api_key or "").lower() == "ollama"
    )
    if not is_ollama:
        return {"configured": False}
    
    base_url = settings.openai_base_url or "http://localhost:11434/v1"
    ollama_url = base_url.replace("/v1", "").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{ollama_url}/api/tags")
            if res.status_code == 200:
                models_data = res.json().get("models", [])
                models = [m.get("name") for m in models_data]
                return {
                    "configured": True,
                    "status": "connected",
                    "models": models,
                    "url": ollama_url
                }
            return {
                "configured": True,
                "status": "error",
                "error": f"HTTP status {res.status_code}",
                "url": ollama_url
            }
    except Exception as e:
        return {
            "configured": True,
            "status": "unreachable",
            "error": str(e),
            "url": ollama_url
        }


@router.get("/health")
async def health_check():
    ollama_info = await _check_ollama_health()
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_model": settings.llm_model,
        "stt_provider": settings.stt_provider,
        "tts_provider": settings.tts_provider,
        "mock_llm": _is_mock_key(),
        "ollama": ollama_info,
        "version": "1.0.0",
    }


@router.get("/")
async def root():
    return {
        "name": "Personal Voice AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
