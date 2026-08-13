"""
Bhojpuri Pronunciation Dictionary Service
Maintains dictionary of core vocabulary, phonetics, regional variants, and phonetic replacements.
Supports dynamic lookup and runtime updates without requiring full model retraining.
"""
from typing import Dict, Any, Optional, List

class BhojpuriDictionary:
    """Manages Bhojpuri pronunciation dictionary and phonetic replacement rules."""

    def __init__(self):
        # Default dictionary loaded from manual specification
        self.dictionary: Dict[str, Dict[str, str]] = {
            "रउआ": {
                "roman": "rauaa",
                "pronunciation": "रउ-आ",
                "meaning": "You (Honorific/Respectful)",
                "variant": "Standard Bhojpuri",
                "example": "रउआ कहाँ जा रहल बानी?"
            },
            "रउरा": {
                "roman": "raura",
                "pronunciation": "रउ-रा",
                "meaning": "Your / You",
                "variant": "Western Bhojpuri",
                "example": "रउरा का हाल बा?"
            },
            "कइसन": {
                "roman": "kaisan",
                "pronunciation": "कै-सन",
                "meaning": "How / What kind of",
                "variant": "Standard Bhojpuri",
                "example": "आज कइसन बा?"
            },
            "कहाँ": {
                "roman": "kahan",
                "pronunciation": "क-हाँ",
                "meaning": "Where",
                "variant": "Standard Bhojpuri",
                "example": "रउआ कहाँ बानी?"
            },
            "बानी": {
                "roman": "baani",
                "pronunciation": "बा-नी",
                "meaning": "Are / Am (Auxiliary Verb)",
                "variant": "Standard Bhojpuri",
                "example": "हम ठीक बानी।"
            },
            "बा": {
                "roman": "baa",
                "pronunciation": "बा",
                "meaning": "Is / Exists",
                "variant": "Standard Bhojpuri",
                "example": "आज मौसम बढ़िया बा।"
            },
            "जातानी": {
                "roman": "jaataani",
                "pronunciation": "जा-ता-नी",
                "meaning": "Going (Present Continuous)",
                "variant": "Standard Bhojpuri",
                "example": "हम बाजार जातानी।"
            },
            "आवतानी": {
                "roman": "aavtaani",
                "pronunciation": "आव-ता-नी",
                "meaning": "Coming",
                "variant": "Standard Bhojpuri",
                "example": "हम अभी आवतानी।"
            },
            "नइखे": {
                "roman": "naikhe",
                "pronunciation": "नई-खे",
                "meaning": "Is not / Does not exist",
                "variant": "Standard Bhojpuri",
                "example": "आज मन ठीक नइखे।"
            },
            "चाहीं": {
                "roman": "chaahin",
                "pronunciation": "चा-हीं",
                "meaning": "Want / Need",
                "variant": "Standard Bhojpuri",
                "example": "रउआ के का चाहीं?"
            },
            "होई": {
                "roman": "hoi",
                "pronunciation": "हो-ई",
                "meaning": "Will happen / Will be",
                "variant": "Standard Bhojpuri",
                "example": "ई काम कब पूरा होई?"
            },
            "भइल": {
                "roman": "bhail",
                "pronunciation": "भ-इल",
                "meaning": "Happened / Became",
                "variant": "Standard Bhojpuri",
                "example": "सच में? ई कब भइल?"
            }
        }

        # Phonetic replacement mapping for TTS mispronunciation corrections
        self.phonetic_replacements: Dict[str, str] = {
            "रउआ": "रउआ",
            "बानी": "बानी",
            "नइखे": "नईखे",
            "रहल": "रहल",
            "जातानी": "जातानी",
        }

    def get_entry(self, word: str) -> Optional[Dict[str, str]]:
        """Retrieve word details from dictionary."""
        return self.dictionary.get(word.strip())

    def add_entry(
        self,
        word: str,
        roman: str,
        pronunciation: str,
        meaning: str,
        variant: str = "Standard Bhojpuri",
        example: str = ""
    ) -> Dict[str, str]:
        """Add or update a word entry dynamically at runtime."""
        entry = {
            "roman": roman,
            "pronunciation": pronunciation,
            "meaning": meaning,
            "variant": variant,
            "example": example
        }
        self.dictionary[word.strip()] = entry
        self.phonetic_replacements[word.strip()] = pronunciation
        return entry

    def apply_phonetic_corrections(self, text: str) -> str:
        """Apply custom phonetic replacements to text before TTS rendering."""
        if not text:
            return ""
        result = text
        for word, phonetic in self.phonetic_replacements.items():
            if word != phonetic:
                result = result.replace(word, phonetic)
        return result

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Return all dictionary entries."""
        return [
            {"word": k, **v}
            for k, v in self.dictionary.items()
        ]

bhojpuri_dictionary = BhojpuriDictionary()
