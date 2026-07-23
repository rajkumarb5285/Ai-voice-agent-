"""
Unit tests for the voice pipeline endpoints (STT and TTS).
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.models.schemas import TranscriptionResponse

@pytest.mark.asyncio
async def test_voices_list(authenticated_client):
    """Verify listing available voices returns list and user current voice."""
    response = await authenticated_client.get("/api/voice/voices")
    assert response.status_code == 200
    data = response.json()
    assert "openai_voices" in data
    assert data["current_voice"] == "alloy"

@pytest.mark.asyncio
async def test_audio_transcription(authenticated_client):
    """Verify STT transcription endpoint."""
    mock_transcription = TranscriptionResponse(
        text="Hello world, this is a test.",
        confidence=0.95,
        language="en",
        duration_seconds=2.5
    )
    
    # Patch transcribe method on the voice API module's stt_service
    with patch("app.api.voice.stt_service.transcribe", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = mock_transcription
        
        # Create a mock webm file
        files = {"audio": ("test.webm", b"mock-webm-data-content", "audio/webm")}
        response = await authenticated_client.post(
            "/api/voice/transcribe",
            files=files,
            data={"language": "en"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello world, this is a test."
        assert data["confidence"] == 0.95
        mock_stt.assert_called_once()

@pytest.mark.asyncio
async def test_audio_synthesis(authenticated_client):
    """Verify TTS synthesis endpoint."""
    mock_audio_bytes = b"mock-mp3-audio-bytes"
    
    # Patch synthesize method on the voice API module's tts_service
    with patch("app.api.voice.tts_service.synthesize", new_callable=AsyncMock) as mock_tts:
        mock_tts.return_value = mock_audio_bytes
        
        response = await authenticated_client.post(
            "/api/voice/synthesize",
            json={"text": "Synthesize this text please", "voice": "alloy"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data
        assert data["content_type"] == "audio/mpeg"
        assert data["size_bytes"] == len(mock_audio_bytes)
        mock_tts.assert_called_once()
