"""
Voice API
POST /voice/transcribe — audio bytes → text (STT)
POST /voice/synthesize — text → audio bytes (TTS)
GET  /voice/synthesize/stream — text → streamed audio
"""
import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.schemas import TranscriptionResponse, TTSRequest
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.utils.logger import logger

router = APIRouter(prefix="/voice", tags=["voice"])

stt_service = STTService()
tts_service = TTSService()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default=None),
    current_user: User = Depends(get_current_user),
):
    """
    Voice Pipeline Step 1: Speech → Text
    Accepts audio file (webm, wav, mp3, ogg) → returns transcribed text
    """
    logger.info(
        "transcribe_request",
        user_id=str(current_user.id),
        filename=audio.filename,
        content_type=audio.content_type,
    )

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=413, detail="Audio file too large (max 25MB)")

    result = await stt_service.transcribe(
        audio_bytes=audio_bytes,
        filename=audio.filename or "audio.webm",
        language=language,
    )

    logger.info("transcription_complete", text_preview=result.text[:50])
    return result


@router.post("/synthesize")
async def synthesize_speech(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Voice Pipeline Step 2: Text → Speech
    Returns MP3 audio bytes as base64 for easy frontend consumption
    """
    logger.info("tts_request", user_id=str(current_user.id), text_length=len(request.text))

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if len(request.text) > 4096:
        raise HTTPException(status_code=400, detail="Text too long (max 4096 chars)")

    # Use user's preferred voice if set
    voice = request.voice or current_user.profile.get("voice", "alloy") if current_user.profile else "alloy"

    audio_bytes = await tts_service.synthesize(
        text=request.text,
        voice=voice,
    )

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {
        "audio_base64": audio_b64,
        "content_type": "audio/mpeg",
        "size_bytes": len(audio_bytes),
    }


@router.post("/synthesize/stream")
async def synthesize_speech_stream(
    request: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Streaming TTS — returns audio as chunked MP3 stream for low-latency playback.
    Frontend can start playing before all audio is generated.
    """
    voice = request.voice or (current_user.profile or {}).get("voice", "alloy")

    async def audio_generator():
        async for chunk in tts_service.synthesize_stream(request.text, voice=voice):
            yield chunk

    return StreamingResponse(
        audio_generator(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/voices")
async def list_voices(current_user: User = Depends(get_current_user)):
    """List available TTS voices."""
    return {
        "openai_voices": [
            {"id": "alloy", "name": "Alloy", "description": "Neutral, balanced"},
            {"id": "nova", "name": "Nova", "description": "Warm, friendly female"},
            {"id": "shimmer", "name": "Shimmer", "description": "Soft, gentle female"},
            {"id": "echo", "name": "Echo", "description": "Deep, resonant male"},
            {"id": "fable", "name": "Fable", "description": "Expressive, storytelling"},
            {"id": "onyx", "name": "Onyx", "description": "Deep, authoritative male"},
        ],
        "current_voice": (current_user.profile or {}).get("voice", "alloy"),
    }
