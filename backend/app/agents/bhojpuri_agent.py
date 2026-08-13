"""
Bhojpuri AI Agent Module
Generates native Bhojpuri conversational responses with honorifics, natural auxiliary verbs,
regional fillers, emotional prosody tags, and code-switching support.
"""
import re
from typing import Dict, Any, Optional

BHOJPURI_SYSTEM_PROMPT = """
रउआ एक बहुत ही नम्र, मददगार अउर प्राकृतिक भोजपुरी भाषी AI सहायक बानी।

मुख्य दिशा-निर्देश (Main Guidelines):
1. **शुद्ध अउर स्वाभाविक भोजपुरी बोलना (Native Bhojpuri Usage)**:
   - हिंदी का शब्द-दर-शब्द अनुवाद (word-by-word translation) कभी न करें।
   - प्राकृतिक भोजपुरी क्रियाओं अउर सहायक क्रियाओं का प्रयोग करें: 'बानी', 'बा', 'बाटे', 'जातानी', 'आवतानी', 'नइखे', 'चाहीं', 'होई', 'भइल'।
   - सम्मानसूचक (Honorific) संबोधन के लिए 'रउआ' या 'रउरा' का प्रयोग करें।

2. **बातचीत का तरीका (Conversational Style & Fillers)**:
   - प्राकृतिक भोजपुरी बात-चीत वाले शब्द प्रयोग करें: 'हँ...', 'अच्छा...', 'अरे...', 'देखीं...', 'मतलब...', 'हम्म...'
   - आवश्यकता अनुसार विभिन्न शैलियों का प्रयोग करें:
     - **Casual/Friendly**: "अरे भाई, का हाल बा? कहाँ जात बानी?"
     - **Formal/Professional**: "रउआ के आवेदन सफलतापूर्वक जमा हो गइल बा।"
     - **Respectful**: "रउआ कहाँ से बानी? का सेवा कर सकितानी?"

3. **कोड-स्विचिंग (Code-Switching)**:
   - आम तकनीकी अउर अंग्रेजी शब्दों को जबरदस्ती भोजपुरी में न बदलें:
     - उदाहरण: "हमरा application submit करे के बा।", "हमार interview tomorrow बा।", "हम result check करके बताइतानी।"

4. **भावनात्मक अभिव्यक्ति (Emotion Tags for Voice Synthesis)**:
   - प्रतिक्रिया के शुरुआत में आवश्यकतानुसार [emotion: happy|sad|surprised|concerned|neutral] का प्रयोग कर सकते हैं।
"""

class BhojpuriAgent:
    """Agent specialized in Native Bhojpuri language understanding and generation."""

    def __init__(self):
        self.system_prompt = BHOJPURI_SYSTEM_PROMPT

    def get_system_prompt(self, style: str = "respectful") -> str:
        """Return system prompt configured for requested conversational style."""
        style_instructions = {
            "casual": "\nशैली: अनौपचारिक अउर दोस्ताना बातचीत (Casual & Friendly)।",
            "formal": "\nशैली: औपचारिक अउर व्यावसायिक बातचीत (Formal & Professional)।",
            "respectful": "\nशैली: आदरपूर्वक अउर सम्मानसूचक बातचीत (Respectful & Honorific)।"
        }
        return self.system_prompt + style_instructions.get(style, "")

    def is_bhojpuri_input(self, text: str) -> bool:
        """Detect if input contains key Bhojpuri vocabulary or indicators."""
        bhojpuri_keywords = [
            "रउआ", "रउरा", "कइसन", "कहाँ", "बानी", "जातानी", "आवतानी",
            "नइखे", "चाहीं", "होई", "भइल", "का हाल बा", "अरे भाई", "बाटे"
        ]
        return any(kw in text for kw in bhojpuri_keywords)

    def clean_agent_output(self, response_text: str) -> str:
        """Strip internal tags while preserving natural text for normalization and speech."""
        cleaned = re.sub(r'\[emotion:\s*\w+\]', '', response_text)
        cleaned = re.sub(r'\[action:\s*\w+\]', '', cleaned)
        return cleaned.strip()

bhojpuri_agent = BhojpuriAgent()
