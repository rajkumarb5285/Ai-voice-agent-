"""
Bhojpuri API Router
Provides endpoints for Bhojpuri text normalization, dictionary lookups, and dynamic word updates.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models.user import User
from app.services.bhojpuri_normalizer import bhojpuri_normalizer
from app.services.bhojpuri_dictionary import bhojpuri_dictionary

router = APIRouter(prefix="/bhojpuri", tags=["bhojpuri"])

class NormalizationRequest(BaseModel):
    text: str

class DictionaryAddRequest(BaseModel):
    word: str
    roman: str
    pronunciation: str
    meaning: str
    variant: str = "Standard Bhojpuri"
    example: str = ""

@router.post("/normalize")
async def normalize_bhojpuri_text(
    request: NormalizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Normalize raw text into spoken Bhojpuri form (numbers, currency, time, etc.)."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    normalized = bhojpuri_normalizer.normalize(request.text)
    phonetic_text = bhojpuri_dictionary.apply_phonetic_corrections(normalized)
    return {
        "original_text": request.text,
        "normalized_text": normalized,
        "phonetic_text": phonetic_text
    }

@router.get("/dictionary")
async def list_dictionary(current_user: User = Depends(get_current_user)):
    """Fetch all entries from the Bhojpuri Pronunciation Dictionary."""
    return {
        "count": len(bhojpuri_dictionary.dictionary),
        "entries": bhojpuri_dictionary.get_all_entries()
    }

@router.post("/dictionary")
async def add_dictionary_entry(
    request: DictionaryAddRequest,
    current_user: User = Depends(get_current_user)
):
    """Dynamically add or update a word entry in the Bhojpuri Pronunciation Dictionary."""
    if not request.word.strip():
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    entry = bhojpuri_dictionary.add_entry(
        word=request.word,
        roman=request.roman,
        pronunciation=request.pronunciation,
        meaning=request.meaning,
        variant=request.variant,
        example=request.example
    )
    return {
        "status": "success",
        "word": request.word,
        "entry": entry
    }
