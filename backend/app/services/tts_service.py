"""
Text-to-Speech Service
Supports: Edge TTS HD Regional Female Neural Voices (Default & Primary) | Google TTS Fallback | OpenAI TTS | ElevenLabs

Voice Pipeline:
  Agent response text → TTSService.synthesize() → audio bytes → stream to browser
"""
import os
import re
import tempfile
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings
from app.utils.logger import logger


class TTSService:
    OPENAI_VOICES = ["alloy", "nova", "shimmer", "echo", "fable", "onyx", "ava"]

    def __init__(self):
        self.provider = settings.tts_provider
        self.openai = AsyncOpenAI(
            api_key=settings.openai_api_key if not settings.openai_base_url else os.environ.get("REAL_OPENAI_API_KEY", settings.openai_api_key)
        )

    def _clean_text_for_speech(self, text: str) -> str:
        """Strip markdown, action tags, section headers, numbered lists, and punctuation artifacts for ultra-natural human conversational speech."""
        # Strip avatar tags like [action: ...] or [emotion: ...]
        t = re.sub(r'\[action:\s*[^\]]+\]', '', text)
        t = re.sub(r'\[emotion:\s*[^\]]+\]', '', t)
        
        # Strip === Agent Output === headers
        t = re.sub(r'===\s*[^=]+\s*===', '', t)
        
        # Strip markdown headers (###, ##, #)
        t = re.sub(r'#+\s*', '', t)
        
        # Strip code blocks
        t = re.sub(r'```[a-zA-Z]*\n[\s\S]*?\n```', ' here is the code snippet. ', t)
        
        # Strip list numbers like "1. ", "2. ", "1) ", "a) "
        t = re.sub(r'\b\d+[\.\)]\s*', ' ', t)
        t = re.sub(r'\b[a-zA-Z][\.\)]\s*', ' ', t)

        # Replace colons and dashes with soft pause commas
        t = re.sub(r'[:–—]', ', ', t)

        # Strip bullet points and bold/italics symbols
        t = re.sub(r'[\*\_\`\~\>•]', '', t)
        
        # Collapse multiple spaces or newlines into smooth spoken pauses
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    async def _synthesize_edge_tts(self, text: str, voice: Optional[str] = None) -> bytes:
        """Synthesize HD sweet female voice using Microsoft Edge Neural Voices across all Indian regional languages."""
        import edge_tts

        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            clean_text = text

        selected_voice = voice
        if not selected_voice or selected_voice.lower() in ["alloy", "nova", "shimmer", "echo", "fable", "onyx", "ava"]:
            # Automatic script-based Indian regional female voice matching
            if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in clean_text):
                if any(c in "ळ" for c in clean_text) or any(w in clean_text for w in ["आहे", "करू", "झाले", "मराठी"]):
                    selected_voice = "mr-IN-AarohiNeural"
                else:
                    selected_voice = "hi-IN-SwaraNeural"
            elif any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in clean_text):
                selected_voice = "bn-IN-TanishaaNeural"
            elif any(ord(c) >= 0x0A00 and ord(c) <= 0x0A7F for c in clean_text):
                selected_voice = "pa-IN-GurpreetNeural"
            elif any(ord(c) >= 0x0A80 and ord(c) <= 0x0AFF for c in clean_text):
                selected_voice = "gu-IN-DhwaniNeural"
            elif any(ord(c) >= 0x0B00 and ord(c) <= 0x0B7F for c in clean_text):
                selected_voice = "or-IN-SubhasiniNeural"
            elif any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in clean_text):
                selected_voice = "ta-IN-PallaviNeural"
            elif any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in clean_text):
                selected_voice = "te-IN-ShrutiNeural"
            elif any(ord(c) >= 0x0C80 and ord(c) <= 0x0CFF for c in clean_text):
                selected_voice = "kn-IN-SapnaNeural"
            elif any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in clean_text):
                selected_voice = "ml-IN-SobhanaNeural"
            elif any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in clean_text):
                selected_voice = "ur-IN-GulNeural"
            else:
                # English (Ava Multilingual Sweet Voice)
                selected_voice = "en-US-AvaMultilingualNeural"

        # Rate "-2%" and Pitch "+3Hz" for warm, sweet natural human conversational cadence
        communicate = edge_tts.Communicate(clean_text, selected_voice, rate="-2%", pitch="+3Hz")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            await communicate.save(tmp_path)
            with open(tmp_path, "rb") as f:
                data = f.read()
            logger.info("edge_tts_complete", voice=selected_voice, audio_bytes=len(data))
            return data
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def _synthesize_google_fallback(self, text: str) -> bytes:
        """Fallback Google Translate TTS for regional languages."""
        import httpx
        from urllib.parse import quote

        clean_text = self._clean_text_for_speech(text)
        if not clean_text:
            clean_text = text

        lang = "en"
        if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in clean_text):
            if any(c in "ळशष" for c in clean_text) and ("आहे" in clean_text or "करू" in clean_text or "झाले" in clean_text):
                lang = "mr"
            else:
                lang = "hi"
        elif any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in clean_text):
            lang = "bn"
        elif any(ord(c) >= 0x0A00 and ord(c) <= 0x0A7F for c in clean_text):
            lang = "pa"
        elif any(ord(c) >= 0x0A80 and ord(c) <= 0x0AFF for c in clean_text):
            lang = "gu"
        elif any(ord(c) >= 0x0B00 and ord(c) <= 0x0B7F for c in clean_text):
            lang = "or"
        elif any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in clean_text):
            lang = "ta"
        elif any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in clean_text):
            lang = "te"
        elif any(ord(c) >= 0x0C80 and ord(c) <= 0x0CFF for c in clean_text):
            lang = "kn"
        elif any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in clean_text):
            lang = "ml"

        url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl={lang}&client=tw-ob&q={quote(clean_text[:200])}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.content

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> bytes:
        """Convert text to audio bytes (MP3)."""
        if not text.strip():
            return b""

        # Primary: High-Definition Regional Sweet Female Voice via Edge TTS
        try:
            return await self._synthesize_edge_tts(text, voice)
        except Exception as ex:
            logger.warning("edge_tts_failed_falling_back_to_google", error=str(ex))

        # Secondary: Google TTS fallback
        try:
            return await self._synthesize_google_fallback(text)
        except Exception as ex:
            logger.warning("google_tts_failed_falling_back_to_openai", error=str(ex))

        # Tertiary: OpenAI / ElevenLabs fallback
        if self.provider == "elevenlabs":
            return await self._synthesize_elevenlabs(text, voice)
        return await self._synthesize_openai(text, voice, speed)

    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks for real-time playback."""
        try:
            audio_bytes = await self.synthesize(text, voice)
            yield audio_bytes
        except Exception as e:
            logger.error("tts_stream_failed", error=str(e))
            import base64
            silent_mp3_b64 = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU3LjU2LjEwMAAAAAAAAAAAAAAA//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGx1bWUsAAAAAAAAAAAAAAA//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGx1bWUsAAAAAAAAAAAAAAA//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGx1bWUsAAAAAAAAAAAAAAA="
            yield base64.b64decode(silent_mp3_b64)

    async def _synthesize_openai(
        self,
        text: str,
        voice: Optional[str],
        speed: float,
    ) -> bytes:
        try:
            voice = voice or settings.tts_voice
            if voice not in self.OPENAI_VOICES:
                voice = "nova"

            clean_text = self._clean_text_for_speech(text)
            response = await self.openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=clean_text,
                response_format="mp3",
                speed=speed,
            )
            return response.content
        except Exception as e:
            logger.error("openai_tts_failed", error=str(e))
            return await self._synthesize_google_fallback(text)

    async def _synthesize_elevenlabs(
        self,
        text: str,
        voice_id: Optional[str],
    ) -> bytes:
        try:
            import httpx
            voice_id = voice_id or settings.elevenlabs_voice_id
            clean_text = self._clean_text_for_speech(text)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": settings.elevenlabs_api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": clean_text,
                        "model_id": "eleven_turbo_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.8,
                            "style": 0.0,
                            "use_speaker_boost": True,
                        },
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error("elevenlabs_tts_failed", error=str(e))
            return await self._synthesize_google_fallback(text)
