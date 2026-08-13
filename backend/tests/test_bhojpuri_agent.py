"""
Unit & Integration Test Suite for Bhojpuri Voice Agent System
"""
import pytest
from app.services.bhojpuri_normalizer import bhojpuri_normalizer
from app.services.bhojpuri_dictionary import bhojpuri_dictionary
from app.agents.bhojpuri_agent import bhojpuri_agent
from app.services.tts_service import TTSService

def test_bhojpuri_currency_normalization():
    result = bhojpuri_normalizer.normalize_currency("कुल खर्च ₹25,000 बा।")
    assert "पच्चीस हजार रुपइया" in result

def test_bhojpuri_time_normalization():
    result = bhojpuri_normalizer.normalize_time("मीटिंग 10:30 AM में बा।")
    assert "साढ़े दस बजे सवेरे" in result

def test_bhojpuri_percentage_normalization():
    result = bhojpuri_normalizer.normalize_percentage("कम से कम 50% काम भइल बा।")
    assert "पचास प्रतिशत" in result

def test_bhojpuri_dictionary_lookup():
    entry = bhojpuri_dictionary.get_entry("रउआ")
    assert entry is not None
    assert entry["roman"] == "rauaa"
    assert entry["meaning"] == "You (Honorific/Respectful)"

def test_bhojpuri_dictionary_dynamic_add():
    word = "का हाल बा"
    new_entry = bhojpuri_dictionary.add_entry(
        word=word,
        roman="ka haal baa",
        pronunciation="का हाल बा",
        meaning="How are you?",
        variant="Standard Bhojpuri"
    )
    assert new_entry["roman"] == "ka haal baa"
    assert bhojpuri_dictionary.get_entry(word) is not None

def test_bhojpuri_agent_detection():
    is_bhoj = bhojpuri_agent.is_bhojpuri_input("रउआ कहाँ जा रहल बानी?")
    assert is_bhoj is True

@pytest.mark.asyncio
async def test_bhojpuri_tts_synthesis():
    tts = TTSService()
    audio_bytes = await tts.synthesize("रउआ कहाँ जा रहल बानी? हम बाजार जातानी।")
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0
