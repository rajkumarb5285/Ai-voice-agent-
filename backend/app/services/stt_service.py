"""
Speech-to-Text Service
Supports: OpenAI Whisper (default) | Deepgram (optional)

Voice Pipeline:
  Browser MediaRecorder → WAV/WEBM blob → POST /api/voice/transcribe
  → STTService.transcribe() → text string → LangGraph agent
"""
import io
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import TranscriptionResponse
from app.utils.logger import logger


class STTService:
    def __init__(self):
        self.provider = settings.stt_provider
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None,
    ) -> TranscriptionResponse:
        """Transcribe raw audio bytes to text."""
        if (settings.openai_api_key.startswith("mock-key") or 
            "mock-key" in settings.openai_api_key or 
            "ollama" in settings.openai_api_key or 
            "11434" in settings.openai_base_url):
            logger.info("mock_stt_transcription_triggered")
            import random
            mock_queries = [
                "Hello Jarvis, how are you today?",
                "What is my top priority tasks today?",
                "Create a reminder for my client call",
                "Give me some wellness guidance"
            ]
            text = random.choice(mock_queries)
            return TranscriptionResponse(
                text=text,
                language="en",
                duration_seconds=2.0
            )

        if self.provider == "deepgram":
            return await self._transcribe_deepgram(audio_bytes, language)
        return await self._transcribe_whisper(audio_bytes, filename, language)

    async def _transcribe_whisper(
        self,
        audio_bytes: bytes,
        filename: str,
        language: Optional[str],
    ) -> TranscriptionResponse:
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            stt_prompt = "यह शुद्ध अवधी, भोजपुरी और हिंदी बोली की रिकॉर्डिंग है। अवधी व भोजपुरी शब्द: अहै, अही, तोहार, करब, अउर, भवा, नीक, बा, बानी, राउर, का हाल अहै।"
            base_url = str(getattr(self.openai, "base_url", "")).lower()
            model_name = "whisper-large-v3-turbo" if "groq" in base_url else "whisper-1"

            stt_lang = "hi"
            if language:
                if language in ["awa-IN", "bho-IN", "bgc-IN", "bra-IN", "mwr-IN", "hi-IN", "hi"]:
                    stt_lang = "hi"
                elif language not in ["auto", ""]:
                    stt_lang = language.split("-")[0] if "-" in language else language


            response = await self.openai.audio.transcriptions.create(
                model=model_name,
                file=(filename, audio_bytes, "audio/webm"),
                prompt=stt_prompt,
                language=stt_lang,
                response_format="verbose_json",
            )


            logger.info(
                "whisper_transcription_complete",
                text_length=len(response.text),
                language=getattr(response, "language", None),
            )

            return TranscriptionResponse(
                text=response.text.strip(),
                language=getattr(response, "language", None),
                duration_seconds=getattr(response, "duration", None),
            )

        except Exception as e:
            logger.error("whisper_transcription_failed", error=str(e))
            raise

    async def _transcribe_deepgram(
        self,
        audio_bytes: bytes,
        language: Optional[str],
    ) -> TranscriptionResponse:
        """Deepgram streaming transcription."""
        try:
            import httpx
            headers = {
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "audio/webm",
            }
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "punctuate": "true",
            }
            if language:
                params["language"] = language

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    content=audio_bytes,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            result = data["results"]["channels"][0]["alternatives"][0]
            return TranscriptionResponse(
                text=result["transcript"].strip(),
                confidence=result.get("confidence"),
            )

        except Exception as e:
            logger.error("deepgram_transcription_failed", error=str(e))
            # Fallback to Whisper
            logger.info("falling_back_to_whisper")
            return await self._transcribe_whisper(audio_bytes, "audio.webm", language)
