from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # App
    environment: str = "development"
    log_level: str = "INFO"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = ["http://localhost:3000"]

    # LLM & Agent
    openai_api_key: str = ""
    groq_api_key: str = ""
    agent_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "gpt-4o-mini"        # Fast + cheap; use gpt-4o for higher quality
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512             # Keep responses concise for low latency
    voice_max_tokens: int = 150           # Hard cap for voice mode — stay under 3 s TTS
    fast_intent_classification: bool = True
    fast_embeddings: bool = True



    # STT / TTS
    stt_provider: str = "whisper"
    tts_provider: str = "openai"
    tts_voice: str = "alloy"
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Web Search
    tavily_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://voice_agent:secret@localhost:5432/voice_agent_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_name: str = "voice_agent_memory"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    # Google OAuth (optional)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Weather (optional)
    openweather_api_key: str = ""

    # LangChain tracing (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""


settings = Settings()


# Monkeypatch ChatOpenAI to optimize Ollama performance
try:
    from langchain_openai import ChatOpenAI
    original_init = ChatOpenAI.__init__

    def patched_init(self, *args, **kwargs):
        # Prevent local LLMs from hanging indefinitely if they get overloaded
        if "timeout" not in kwargs:
            kwargs["timeout"] = 60.0

        # Determine if base_url or api_key points to Ollama
        base_url = kwargs.get("base_url") or getattr(self, "base_url", None) or settings.openai_base_url or ""
        api_key = kwargs.get("api_key") or getattr(self, "api_key", None) or settings.openai_api_key or ""
        
        is_ollama = "ollama" in str(api_key).lower() or "11434" in str(base_url) or "host.docker.internal" in str(base_url)
        if is_ollama:
            extra_body = kwargs.get("extra_body") or {}
            # Keep Ollama models loaded in memory/GPU permanently to prevent cold starts
            if "keep_alive" not in extra_body:
                extra_body["keep_alive"] = -1
            kwargs["extra_body"] = extra_body
        original_init(self, *args, **kwargs)

    ChatOpenAI.__init__ = patched_init
except Exception:
    pass

