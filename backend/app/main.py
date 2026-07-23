"""
Personal Voice AI Agent — FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
import os

if settings.openai_base_url:
    os.environ["OPENAI_BASE_URL"] = settings.openai_base_url

# If mock API key is set, mock ChatOpenAI globally for offline development compatibility
if settings.openai_api_key.startswith("mock-key") or "mock-key" in settings.openai_api_key:
    import json
    import sys
    import asyncio
    
    class MockAIMessage:
        def __init__(self, content: str):
            self.content = content

    class MockAIMessageChunk:
        def __init__(self, content: str):
            self.content = content

    class MockChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass

        def _detect_lang(self, query: str) -> str:
            q = query.lower()
            # Malayalam (U+0D00–U+0D7F) — must check before Hindi/other Devanagari
            if "malayalam" in q or "മലയാളം" in q or any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in query):
                return "malayalam"
            # Punjabi / Gurmukhi (U+0A00–U+0A7F)
            if "punjabi" in q or "ਪੰਜਾਬੀ" in q or any(ord(c) >= 0x0A00 and ord(c) <= 0x0A7F for c in query):
                return "punjabi"
            if "hindi" in q or "हिंदी" in q or "bhojpuri" in q or "भोजपुरी" in q or "haryanvi" in q or "हरियाणवी" in q or "awadhi" in q or "अवधी" in q or "braj" in q or "ब्रज" in q or "marwari" in q or "मारवाड़ी" in q or any(c in query for c in "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"):
                if "bhojpuri" in q or "भोजपुरी" in q or "प्रणाम" in q or "राउर" in q or "बानी" in q or "हमार" in q:
                    return "bhojpuri"
                if "haryanvi" in q or "हरियाणवी" in q or "मन्ने" in q or "तन्ने" in q or "क्यूकर" in q or "सैं" in q:
                    return "haryanvi"
                if "awadhi" in q or "अवधी" in q or "अहै" in q or "काहे" in q or "जेन" in q:
                    return "awadhi"
                if "braj" in q or "ब्रज" in q or "मेरो" in q or "करीजै" in q or "नयौ" in q:
                    return "braj bhasha"
                if "marwari" in q or "मारवाड़ी" in q or "कांई" in q or "कठै" in q or "अठै" in q or "म्हारो" in q:
                    return "marwari"
                if "marathi" in q or "मराठी" in q or q.strip().endswith("आहे") or q.strip().endswith("करा") or q.strip().endswith("करू"):
                    return "marathi"
                return "hindi"
            if "kannada" in q or "ಕನ್ನಡ" in q or any(ord(c) >= 0x0C80 and ord(c) <= 0x0CFF for c in query):
                return "kannada"
            if "telugu" in q or "తెలుగు" in q or any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in query):
                return "telugu"
            if "tamil" in q or "தமிழ்" in q or any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in query):
                return "tamil"
            if "marathi" in q or "मराठी" in q:
                return "marathi"
            if "bengali" in q or "বাংলা" in q or any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in query):
                return "bengali"
            if "odia" in q or "ଓଡ଼ିଆ" in q or any(ord(c) >= 0x0B00 and ord(c) <= 0x0B7F for c in query):
                return "odia"
            if "gujarati" in q or "ગુજરાતી" in q or any(ord(c) >= 0x0A80 and ord(c) <= 0x0AFF for c in query):
                return "gujarati"
            return "english"

        def _get_structured_response(self, query: str, lang: str = "english") -> str:
            q = query.lower()
            
            # Sub-category detection
            category = "default"
            if "structure automation" in q or "structured output" in q or "schema" in q or "pydantic" in q:
                category = "schema"
            elif "task" in q or "priority" in q or "todo" in q or "schedule" in q or "calendar" in q:
                category = "tasks"
            elif "wellness" in q or "health" in q or "stress" in q or "sleep" in q:
                category = "wellness"
            elif "coding" in q or "python" in q or "code" in q or "programming" in q:
                category = "coding"
            elif "email" in q or "mail" in q:
                category = "email"

            # Multi-lingual templates
            templates = {
                "punjabi": {
                    "schema": "### LLM ਸਕੀਮਾ ਅਤੇ ਬਣਤਰ ਆਟੋਮੇਸ਼ਨ",
                    "tasks": "### ਕਾਰਜ ਪ੍ਰਬੰਧਨ:\n1. **ਬੈਕਐਂਡ ਕੰਮ**: JWT ਪ੍ਰਮਾਣਿਕਤਾ ਅਤੇ SQLite ਜਾਂਚੋ।\n2. **ਵੈੱਬਸਾਕਿਟ ਸਥਿਰਤਾ**: ਮੁੜ-ਕਨੈਕਟ ਹੋਣ ਦੇ ਸਮੇਂ ਨੂੰ ਅਨੁਕੂਲ ਬਣਾਓ।",
                    "wellness": "### 🧘 ਤੰਦਰੁਸਤੀ ਅਤੇ ਪ੍ਰਦਰਸ਼ਨ ਅਨੁਕੂਲਤਾ\n- **ਛੋਟਾ ਬ੍ਰੇਕ**: 20-20-20 ਨਿਯਮ ਦੀ ਪਾਲਣਾ ਕਰੋ।\n- **ਸਾਹ ਲੈਣ ਦੀ ਕਸਰਤ**: ਤਣਾਅ ਘਟਾਉਣ ਲਈ 4-7-8 ਬਾਕਸ ਬ੍ਰੀਥਿੰਗ ਕਰੋ।",
                    "coding": "### 💻 ਪਾਈਥਨ ਕੋਡਿੰਗ ਸਹਾਇਤਾ\nFastAPI ਦੀ ਵਰਤੋਂ ਕਰਕੇ ਮਾਡਿਊਲਰ ਰਾਊਟਿੰਗ ਦਾ ਉਦਾਹਰਨ।",
                    "email": "### ✉️ ਈਮੇਲ ਆਟੋਮੇਸ਼ਨ\nਤੁਹਾਡਾ ਈਮੇਲ ਡਰਾਫਟ ਤਿਆਰ ਹੈ।",
                    "default": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਨਿੱਜੀ ਵੌਇਸ ਏਆਈ ਸਹਾਇਕ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
                },
                "malayalam": {
                    "schema": "### LLM സ്കീമയും സ്ട്രക്ചർ ഓട്ടോമേഷനും",
                    "tasks": "### മുൻഗണനാ ജോലികൾ:\n1. **ബാക്കെൻഡ് ജോലികൾ**: JWT ഓതന്റിക്കേഷനും SQLite-ഉം പരിശോധിക്കുക.\n2. **വെബ്സോക്കറ്റ് സ്ഥിരത**: കണക്ഷൻ പ്രശ്നങ്ങൾ പരിഹരിക്കുക.",
                    "wellness": "### 🧘 ആരോഗ്യവും ജീവിതശൈലിയും\n- **ചെറിയ ഇടവേള**: 20-20-20 നിയമം പാലിക്കുക.\n- **ശ്വാസക്രിയ വ്യായാമം**: സ്ട്രെസ്സ് കുറയ്ക്കാൻ 4-7-8 ബോക്സ് ശ്വസനം ചെയ്യുക.",
                    "coding": "### 💻 പൈത്തൺ കോഡിംഗ് സഹായം\nFastAPI ഉപയോഗിച്ചുള്ള റൂട്ടിംഗ് ഉദാഹരണം.",
                    "email": "### ✉️ ഇമെയിൽ ഓട്ടോമേഷൻ\nനിങ്ങളുടെ ഇമെയിൽ ഡ്രാഫ്റ്റ് തയ്യാറാണ്.",
                    "default": "ഹലോ! ഞാൻ നിങ്ങളുടെ പേഴ്സണൽ വോയിസ് എഐ അസിസ്റ്റന്റ് ആണ്. ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?"
                },
                "haryanvi": {
                    "schema": "### LLM स्कीमा और ढांचा स्वचालन",
                    "tasks": "### 📋 खास काम:\n1. **बैकएंड काम**: JWT ऑथेंटिकेशन और SQLite जांचो।\n2. **वेबसॉकेट स्थिरता**: डिस्कनेक्शन ठीक करो।",
                    "wellness": "### 🧘 सेहत और काम की बातां\n- **छोटा ब्रेक**: 20-20-20 नियम मानो।\n- **सांस की कसरत**: तनाव घटाण खातिर 4-7-8 बॉक्स ब्रीदिंग करो।",
                    "coding": "### 💻 पायथन कोडिंग सहायता\nFastAPI राउटिंग का एक उदाहरण देखो।",
                    "email": "### ✉️ ईमेल स्वचालन\nथारा पेंडिंग ईमेल का ड्राफ्ट त्यार सै।",
                    "default": "राम राम जी! मैं थारा पर्सनल वॉयस एआई असिस्टेंट हूँ। आज मैं थारी के मदद कर सकूँ हूँ?"
                },
                "awadhi": {
                    "schema": "### LLM स्कीमा अउर ढांचा स्वचालन",
                    "tasks": "### 📋 जरुरी काम:\n1. **बैकएंड काम**: JWT ऑथ अउर SQLite जांचा।\n2. **वेबसॉकेट स्थिरता**: डिस्कनेक्ट होय का ठीक करा।",
                    "wellness": "### 🧘 सेहत अउर काम का अनुकूलन\n- **छोट ब्रेक**: 20-20-20 नियम माना।\n- **सांस का व्यायाम**: तनाव कम करै बरे 4-7-8 बॉक्स ब्रीदिंग करा।",
                    "coding": "### 💻 पाइथन कोडिंग सहायता\nFastAPI राउटिंग का एक उदाहरण इहाँ है।",
                    "email": "### ✉️ ईमेल स्वचालन\nतुम्हार पेंडिंग ईमेल का ड्राफ्ट त्यार अहै।",
                    "default": "प्रणाम! हम तुम्हार पर्सनल वॉयस एआई असिस्टेंट अही। आज हम तुम्हार का सहायता करी?"
                },
                "braj bhasha": {
                    "schema": "### LLM स्कीमा और ढांचा स्वचालन",
                    "tasks": "### 📋 मुख्य काज:\n1. **बैकएंड काज**: JWT ऑथेंटिकेशन और SQLite जांचौ।\n2. **वेबसॉकेट स्थिरता**: रीकनेक्शन सुधारौ।",
                    "wellness": "### 🧘 स्वास्थ्य और जीवनशैली अनुकूलन\n- **छोटौ विराम**: 20-20-20 नियम पालौ।\n- **प्राणायाम**: तनाव कम करिवे कूँ 4-7-8 बॉक्स प्राणायाम करौ।",
                    "coding": "### 💻 पायथन कोडिंग सहायता\nFastAPI राउटिंग कौ उदाहरण देखो।",
                    "email": "### ✉️ ईमेल स्वचालन\nतिहारौ ईमेल ड्राफ्ट त्यार है।",
                    "default": "राधे राधे! मैं तिहारौ पर्सनल वॉयस एआई असिस्टेंट हूँ। आज मैं तिहारी कहा मदद करूँ?"
                },
                "marwari": {
                    "schema": "### LLM स्कीमा अर ढांचा स्वचालन",
                    "tasks": "### 📋 म्हारा मुख्य काम:\n1. **बैकएंड काम**: JWT ऑथेंटिकेशन अर SQLite जांचो।\n2. **वेबसॉकेट स्थिरता**: कनेक्शन ठीक करो।",
                    "wellness": "### 🧘 सेहत अर काम री बातां\n- **छोटौ ब्रेक**: 20-20-20 नियम मानो।\n- **सांस रो व्यायाम**: तनाव कम करण सारू 4-7-8 बॉक्स ब्रीदिंग करो।",
                    "coding": "### 💻 पायथन कोडिंग मदद\nFastAPI राउटिंग रो एक उदाहरण अरठै है।",
                    "email": "### ✉️ ईमेल स्वचालन\nथारो ईमेल ड्राफ्ट त्यार है।",
                    "default": "खम्मा घणी! मैं थਾਰോ खुद को वॉयस एआई असिस्टेंट हूँ। आज मैं थारी कांई मदद करूँ?"
                },
                "hindi": {
                    "schema": "### LLM स्कीमा और संरचना स्वचालन\n\nLLM संरचना स्वचालन का अर्थ है असंरचित पाठ इनपुट से संरचित डेटा (आमतौर पर JSON) निकालना।\n\n#### 1. मुख्य अवधारणाएं\n- **Pydantic स्कीमा**: सटीक नियमों के साथ अपने डेटा मॉडल को परिभाषित करें।\n- **Instructor**: Pydantic स्कीमा लागू करने के लिए एक सरल रैपर।",
                    "tasks": "### कार्य प्रबंधन और उत्पादकता विश्लेषण\n\nयहाँ आपकी वर्तमान कार्यसूची का विवरण दिया गया है:\n\n#### 📋 प्राथमिकता वाले कार्य:\n1. **बैकएंड एकीकरण**: JWT ऑथेंटिकेशन और लोकल SQLite डेटाबेस को सत्यापित करें।\n2. **वेबसॉकेट स्थिरता**: रीकनेक्ट अंतराल को अनुकूलित करें और अचानक सॉकेट डिस्कनेक्ट होने की समस्या को हल करें।\n3. **वॉयस मोड परीक्षण**: Base64-एन्कोडेड बफ़र्स का उपयोग करके ऑडियो चंक्स स्ट्रीमिंग की जांच करें।",
                    "wellness": "### 🧘 स्वास्थ्य और जीवनशैली अनुकूलन\n\nतनाव कम करने और ऊर्जा बनाए रखने के लिए:\n- **छोटा ब्रेक**: 20-20-20 नियम का पालन करें। हर 20 मिनट में 20 फीट दूर किसी वस्तु को 20 सेकंड के लिए देखें।\n- **श्वसन व्यायाम**: तनाव कम करने के लिए 4-7-8 बॉक्स ब्रीदिंग करें।\n- **हाइड्रेशन**: हर घंटे 250 मिलीलीटर पानी पीने का लक्ष्य रखें।",
                    "coding": "### 💻 पायथन कोडिंग सहायता\n\nFastAPI का उपयोग करके मॉड्यूल राउटिंग का उदाहरण:\n```python\nfrom fastapi import APIRouter\nrouter = APIRouter(prefix=\"/api/tasks\", tags=[\"tasks\"])\n```",
                    "email": "### ✉️ ईमेल स्वचालन\n\nयहाँ आपके लंबित कार्यों के लिए एक ईमेल ड्राफ्ट है:\n\n**विषय**: एआई वॉयस एजेंट की प्रगति पर अपडेट\n\nप्रिय क्लाइंट, मुझे यह बताते हुए खुशी हो रही है कि एआई वॉयस एजेंट स्थानीय वातावरण में पूरी तरह कार्यात्मक है।",
                    "default": "नमस्ते! मैं आपका पर्सनल एआई असिस्टेंट हूँ। आज मैं आपकी क्या मदद कर सकता हूँ?"
                },
                "bhojpuri": {
                    "schema": "### LLM स्कीमा आ ऑटोमेशन\n\nअसंरचित पाठ से संरचित डेटा निकाले के काम।",
                    "tasks": "### 📋 मुख्य काम:\n1. **बैकएंड काम**: JWT ऑथ आ SQLite डेटाबेस चेक करीं।\n2. **वेबसॉकेट स्थिरता**: डिस्कनेक्शन के ठीक करीं।",
                    "wellness": "### 🧘 सेहत आ काम के सुधार\n- **छोटका ब्रेक**: 20-20-20 नियम मानीं।\n- **सांस के कसरत**: तनाव कम करे खातिर 4-7-8 बॉक्स ब्रीदिंग करीं।",
                    "coding": "### 💻 पाइथन कोडिंग सहायता\nFastAPI राउटिंग के एगो उदाहरण देखल जाव।",
                    "email": "### ✉️ ईमेल ऑटोमेशन\nराउर पेंडिंग ईमेल के ड्राफ्ट इहाँ बा।",
                    "default": "प्रणाम! हम राउर पर्सनल आवाज एआई सहायक बानी। आज हम राउर कइसे मदद करीं?"
                },
                "marathi": {
                    "schema": "### LLM स्कीमा आणि ऑटोमेशन\n\nअसंरचित मजकुरातून संरचित माहिती काढणे.",
                    "tasks": "### 📋 प्राथमिक कामे:\n1. **बॅकएंड एकत्रीकरण**: JWT ऑथ आणि SQLite डेटाबेस तपासा.\n2. **वेबसॉकेट स्थिरता**: रीकनेक्शन सुधारा.",
                    "wellness": "### 🧘 निरोगी जीवनशैली आणि कार्यक्षमता वाढवणे\n- **लहान ब्रेक**: 20-20-20 नियमाचे पालन करा.\n- **श्वसन व्यायाम**: तणाव कमी करण्यासाठी 4-7-8 बॉक्स ब्रीदिंग करा.",
                    "coding": "### 💻 पायथन कोडिंग मदत\nFastAPI मॉड्यूल राउटिंगचे उदाहरण.",
                    "email": "### ✉️ ईमेल ऑटोमेशन\nतुमच्यासाठी ईमेलचा मसुदा खालीलप्रमाणे आहे.",
                    "default": "नमस्कार! मी तुमचा वैयक्तिक व्हॉइस एआय असिस्टंट आहे. आज मी तुम्हाला कशी मदत करू शकतो?"
                },
                "kannada": {
                    "schema": "### LLM ಸ್ಕೀಮಾ ಮತ್ತು ರಚನೆ ಆಟೊಮೇಷನ್\n\nಅಸಂಘಟಿತ ಪಠ್ಯದಿಂದ ಸಂಘಟಿತ ಡೇಟಾ (JSON) ಹೊರತೆಗೆಯುವುದು ಇದರ ಉದ್ದೇಶವಾಗಿದೆ.",
                    "tasks": "### ಕಾರ್ಯ ನಿರ್ವಹಣೆ ಮತ್ತು ಉತ್ಪಾದಕತೆ ವಿಶ್ಲೇಷಣೆ\n\n#### 📋 ಆದ್ಯತೆಯ ಕೆಲಸಗಳು:\n1. **ಬ್ಯಾಕೆಂಡ್ ಸಂಯೋಜನೆ**: JWT ದೃಢೀಕರಣ ಮತ್ತು ಸ್ಥಳೀಯ SQLite ಡೇಟಾಬೇಸ್ ಪರಿಶೀಲಿಸಿ.\n2. **ವೆಬ್\u200cಸಾಕೆಟ್ ಸ್ಥಿರತೆ**: ಮರುಸಂಪರ್ಕ ಸಮಯವನ್ನು ಉತ್ತಮಗೊಳಿಸಿ.",
                    "wellness": "### 🧘 ಕ್ಷೇಮ ಮತ್ತು ಕಾರ್ಯಕ್ಷಮತೆ ಉತ್ತಮಗೊಳಿಸುವಿಕೆ\n- **ಸಣ್ಣ ವಿರಾಮ**: 20-20-20 ನಿಯಮವನ್ನು ಪಾಲಿಸಿ. ಪ್ರತಿ 20 ನಿಮಿಷಕ್ಕೆ 20 ಅಡಿ ದೂರದಲ್ಲಿರುವ ವಸ್ತುವನ್ನು 20 ಸೆಕೆಂಡುಗಳ ಕಾಲ ನೋಡಿ.\n- **ಉಸಿರಾಟದ ವ್ಯಾಯામ**: ಒತ್ತಡ నివారణೆಗೆ 4-7-8 ಬಾಕ್ಸ್ ಉಸಿರಾಟದ ಕ್ರಿಯೆ ಮಾಡಿ.",
                    "coding": "### 💻 ಪೈಥಾನ್ ಕೋಡಿಂಗ್ ಸಹಾಯ\nFastAPI ಬಳಸಿಕೊಂಡು ಮಾಡ್ಯುಲರ್ ರೂಟಿಂಗ್ ಪ್ರದರ್ಶಿಸುವ ಕೋಡ್ ಇಲ್ಲಿದೆ:\n```python\nfrom fastapi import APIRouter\nrouter = APIRouter(prefix=\"/tasks\")\n```",
                    "email": "### ✉️ ಇಮೇಲ್ ಆಟೊಮೇಷನ್\nನಿಮ್ಮ ಇಮೇಲ್\u200cಗಾಗಿ ਕਰੜੂ ಇಲ್ಲಿದೆ:\n**ವಿಷಯ**: ಧ್ವನಿ ಎഐ ಪ್ರಗತಿ ವರದಿ",
                    "default": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಧ್ವನಿ ಎഐ ಸಹಾಯಕ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"
                },
                "telugu": {
                    "schema": "### LLM నిర్మాణం మరియు స్కీమా ఆటోమేషన్",
                    "tasks": "### ప్రాధాన్యత పనులు:\n1. **బ్యాకెండ్ ఇంటిగ్రేషన్**: JWT ప్రమాణీకరణ మరియు SQLite డేటాబేస్ తనిఖీ చేయండి.\n2. **వెబ్\u200cసాకెట్ స్థిరత్వం**: కనెక్షన్ డిస్కనెక్ట్ సమస్యలను పరిష్కరించండి.",
                    "wellness": "### 🧘 వెల్నెస్ మరియు పనితీరు ఆప్టిమైజేషన్\n- **చిన్న విరామం**: 20-20-20 నియమాన్ని పాటించండి.\n- **శ్లేష వ్యాయామం**: 4-7-8 బాక్స్ శ్వాస తీసుకోండి.",
                    "coding": "### 💻 పైథాన్ కోడింగ్ సహాయం\nFastAPI ద్వారా వెబ్ రూటింగ్ ఉదాహరణ.",
                    "email": "### ✉️ ఈమెయిల్ ఆటోమేషన్\nమీ పెండింగ్ ఈమెయిల్ కరడు సిద్ధంగా ఉంది.",
                    "default": "నమస్కారం! నేను మీ వ్యక్తిగత వాయిస్ ఏఐ అసిస్టెంట్ ని. ఈ రోజు మీకు ఎలా సహాయపడగలను?"
                },
                "tamil": {
                    "schema": "### LLM கட்டமைப்பு மற்றும் ஸ்கீமா ஆட்டோমেஷன்",
                    "tasks": "### 📋 முன்னுரிமை பணிகள்:\n1. **பின்தள ஒருங்கிணைப்பு**: JWT அங்கீகாரம் மற்றும் SQLite தரவுத்தளத்தை சரிபார்க்கவும்.\n2. **வெப்சாக்கெட் நிலைத்தன்மை**: மறுஇணைப்பு நேரத்தை மேம்படுத்தவும்.",
                    "wellness": "### 🧘 ஆரோக்கியம் மற்றும் செயல்திறன் மேம்பாடு\n- **சிறிய இடைவெளி**: 20-20-20 விதியைப் பின்பற்றுங்கள்.\n- **மூச்சுப்பயிற்சி**: மன அழுத்தத்தைக் குறைக்க 4-7-8 மூச்சுப்பயிற்சி செய்யவும்.",
                    "coding": "### 💻 பைதான் கோடிங் உதவி\nFastAPI ரூட்டிங் உதாரணம் இங்கே உள்ளது.",
                    "email": "### ✉️ மின்னஞ்சல் ஆட்டოமேশন\nமின்னஞ்சல் வரைவு தயாராக உள்ளது.",
                    "default": "வணக்கம்! நான் உங்கள் தனிப்பட்ட குரல் AI உதவியாளர். இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?"
                },
                "bengali": {
                    "schema": "### LLM স্কিমা ও অটোমেশন",
                    "tasks": "### 📋 অগ্রাধিকারমূলক কাজ:\n1. **ব্যাকএন্ড ইন্টিগ্রেশন**: JWT অথেনটিকেশন ও SQLite ডাটাবেস পরীক্ষা করুন।\n2. **ওয়েবসকেট স্থিতিশীলতা**: সংযোগ বিচ্ছিন্ন সমস্যা সমাধান করুন।",
                    "wellness": "### 🧘 সুস্থতা ও কর্মক্ষমতা বৃদ্ধি\n- **ছোট বিরতি**: 20-20-20 নিয়ম মেনে চলুন।\n- **শ্বাস-প্রশ্বাসের ব্যায়াম**: চাপ কমাতে 4-7-8 বক্স ব্রিদিং করুন।",
                    "coding": "### 💻 পাইথন কোডিং সহায়তা\nFastAPI ব্যবহার করে মডুলার রাউটিং-এর একটি উদাহরণ দেওয়া হলো।",
                    "email": "### ✉️ ইমেল অটোমেশন\nআপনার মুলতুবি ইমেলের একটি খসড়া এখানে রয়েছে।",
                    "default": "নমস্কার! আমি আপনার ব্যক্তিগত ভয়েস এআই সহকারী। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
                },
                "odia": {
                    "schema": "### LLM ସ୍କିମା ଏବଂ ଅଟୋମେସନ",
                    "tasks": "### 📋 ପ୍ରାଥମିକ କାର୍ଯ୍ୟ:\n1. **ବ୍ୟାକଏଣ୍ଡ ସଂଯୋଗ**: JWT ଅଥେଣ୍ଟିକେସନ ଓ SQLite ଡାଟାବେସ ଯାଞ୍ચ କରନ୍ତୁ।\n2. **ୱେବସକେଟ ସ୍ଥିରତା**: ରିକନେକ୍ଟ ସମୟକୁ ସୁଧାରନ୍ତୁ।",
                    "wellness": "### 🧘 ସ୍ୱାସ୍ଥ୍ୟ ଏବଂ କାର୍ଯ୍ୟଦକ୍ଷତା ବୃଦ୍ଧି\n- **ଛୋଟ ବିରତି**: 20-20-20 ନିୟମ ପାଳନ କରନ୍ତୁ।\n- **ଶ୍ୱାସକ୍ରିୟା ବ୍ୟାୟାମ**: ଚିନ୍ତା ଦୂର କରିବା ପାଇଁ 4-7-8 ବକ୍ସ ବ୍ରିଦିଂ କରନ୍ତୁ।",
                    "coding": "### 💻 ପାଇଥନ କୋଡିଂ ସହାୟତା\nFastAPI ବ୍ୟવହାର କରି କୋଡ ରୁଟିଂର ଏକ ଉଦାହରଣ ଏଠାରେ ଦିଆଗଲା।",
                    "email": "### ✉️ ଇମେଲ ଅଟୋମେସନ\nଆପଣଙ୍କର ପେଣ୍ଡିଂ ଇମେଲର ଚିଠା ଏଠାରେ ଅଛି।",
                    "default": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କ ବ୍ୟକ୍ତିଗତ ଭଏସ୍ ଏଆଇ ସହକାରୀ। ଆଜି ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ್ಯ କରିପାରିବି?"
                },
                "gujarati": {
                    "schema": "### LLM સ્કીમા અને ઓટોમેશન",
                    "tasks": "### 📋 અગ્રતાના કાર્યો:\n1. **બેકએન્ડ એકીકરણ**: JWT ઓથેન્ટિકેશન અને SQLite ડેટાબેઝ ચકાસો।\n2. **વેબસોર્કેટ સ્થિરતા**: ડિસ્કનેક્શન સમસ્યાઓ દૂર કરો।",
                    "wellness": "### 🧘 સુખાકારી અને કાર્યક્ષમતા\n- **નાનો વિરામ**: 20-20-20 નિયમનું પાલન કરો.\n- **શ્વાસોચ્છવાસની કસરત**: તણાવ ઓછો કરવા માટે 4-7-8 બોક્સ બ્રીધિંગ કરો।",
                    "coding": "### 💻 પાયથન કોડિંગ સહાય\nFastAPI નો ઉપયોગ કરીને રાઉટિંગનું ઉદાહરણ નીચે મુજબ છે.",
                    "email": "### ✉️ ઈમેલ ઓટોમેશન\nતમારા ઈમેલનો મુસદ્દો નીચે મુજબ છે.",
                    "default": "નમસ્તે! હું તમારો પર્સનલ વોઇસ એઆઇ આસિસ્ટન્ટ છું. આજે હું તમને કેવી રીતે મદદ કરી શકું?"
                },
                "english": {
                    "schema": "### LLM Structure Automation & Schema Extraction\n\nLLM Structure Automation is the practice of extracting structured, schema-conforming data (typically JSON) from unstructured text inputs.\n\n#### 1. Core Abstractions\n- **Pydantic Schemas**: Define your data models with precise type constraints and validation rules.\n- **Instructor**: A lightweight wrapper for OpenAI/Anthropic SDKs that enforces Pydantic schemas.\n- **LangChain Structured Output**: Using `.with_structured_output()` to automatically parse outputs into Pydantic models.\n\n#### 2. Standard Implementation (Python)\n```python\nfrom pydantic import BaseModel, Field\nfrom openai import OpenAI\nimport instructor\n\n# Define target schema\nclass UserDetails(BaseModel):\n    name: str = Field(description=\"The user's full name\")\n    email: str = Field(description=\"The user's email address\")\n\n# Patch client\nclient = instructor.patch(OpenAI())\n\n# Retrieve structured data\nuser: UserDetails = client.chat.completions.create(\n    model=\"gpt-4o\",\n    response_model=UserDetails,\n    messages=[{\"role\": \"user\", \"content\": \"Extract: Rajkumar, rajkumar@example.com\"}]\n)\n```",
                    "tasks": "### Task Management & Productivity Analysis\n\nHere is a structured breakdown of your current agenda and pending automation tasks:\n\n#### 📋 Priority Tasks:\n1. **Backend Integration**: Verify the JWT auth middleware and SQLite database initialization.\n2. **WebSocket Stability**: Optimize reconnect intervals and handle unexpected socket disconnections.\n3. **Voice Mode Testing**: Validate audio chunk streaming using base64-encoded buffers.\n\n#### 📅 Scheduled Actions:\n- **Daily Standup**: Sync with team on local development setup (10:00 AM).\n- **Code Review**: Review LangGraph multi-agent routing configurations (2:00 PM).",
                    "wellness": "### Wellness & Performance Optimization\n\nMaintaining focus and physical wellness is critical during high-intensity coding sessions.\n\n#### 🧘 Recommendations:\n- **Micro-breaks**: Follow the 20-20-20 rule. Look at something 20 feet away for 20 seconds every 20 minutes.\n- **Breathing Exercise**: 4-7-8 box breathing to reduce stress.\n- **Hydration**: Aim for 250ml of water every hour.",
                    "coding": "### Python Coding Assistance\n\nHere is a structured example demonstrating modular routing using FastAPI:\n\n```python\nfrom fastapi import APIRouter, Depends\nfrom sqlalchemy.ext.asyncio import AsyncSession\n\nrouter = APIRouter(prefix=\"/api/tasks\", tags=[\"tasks\"])\n\n@router.get(\"/\")\nasync def get_tasks(db: AsyncSession = Depends(get_db)):\n    # Retrieve priority tasks from the local SQLite engine\n    tasks = await db.execute(select(Task).order_by(Task.priority))\n    return tasks.scalars().all()\n```",
                    "email": "### Email Automation & Synthesis\n\nHere is a draft response for your pending communication:\n\n**Subject**: Re: Progress Update on AI Voice Agent Local Workspace\n\nDear Client,\n\nI am pleased to report that the AI Voice Agent is now fully operational in the local environment. All backend service nodes (Intent Classification, Short-term/Episodic Memory, and Research Tools) are integrated with the local SQLite database.\n\nBest regards,\nYour AI Assistant",
                    "default": "Hello! I am Javis, your personal AI assistant. How can I help you today?"
                }
            }

            lang_dict = templates.get(lang, templates["english"])
            return lang_dict.get(category, lang_dict["default"])

        async def ainvoke(self, messages, *args, **kwargs):
            system_content = ""
            human_content = ""
            for m in messages:
                if hasattr(m, "content"):
                    if m.__class__.__name__ == "SystemMessage":
                        system_content = m.content
                    elif m.__class__.__name__ == "HumanMessage":
                        human_content = m.content
                    else:
                        if not system_content and not human_content:
                            human_content = m.content

            # Detect query language
            lang = self._detect_lang(human_content)

            # Case 1: Intent Classifier
            if "intent classifier" in system_content.lower() or "intent categories" in system_content.lower():
                intent = "general_chat"
                agent = "orchestrator"
                text = human_content.lower()
                
                if any(k in text for k in ["search", "google", "weather", "news", "find", "research"]):
                    intent = "research"
                    agent = "research_agent"
                elif any(k in text for k in ["code", "python", "javascript", "program", "function", "bug", "compile", "script"]):
                    intent = "coding"
                    agent = "coding_agent"
                elif any(k in text for k in ["plan", "goal", "breakdown", "todo", "steps"]):
                    intent = "planning"
                    agent = "planner_agent"
                elif any(k in text for k in ["task", "reminder", "calendar", "schedule", "event", "meeting"]):
                    intent = "productivity"
                    agent = "productivity_agent"
                elif any(k in text for k in ["learn", "study", "explain", "understand", "concept", "course"]):
                    intent = "learning"
                    agent = "learning_agent"
                elif any(k in text for k in ["wellness", "fitness", "health", "diet", "sleep", "stress"]):
                    intent = "wellness"
                    agent = "wellness_agent"
                elif any(k in text for k in ["career", "job", "resume", "interview"]):
                    intent = "career"
                    agent = "career_agent"
                elif any(k in text for k in ["email", "mail", "inbox", "gmail"]):
                    intent = "email"
                    agent = "email_agent"
                elif any(k in text for k in ["remember", "forget", "recall", "memory"]):
                    intent = "memory"
                    agent = "memory_agent"

                response_data = {
                    "intent": intent,
                    "confidence": 0.95,
                    "sub_intents": [],
                    "entities": {},
                    "selected_agents": [agent] if agent != "orchestrator" else ["research_agent"],
                    "response_mode": "conversational"
                }
                return MockAIMessage(json.dumps(response_data))

            # Case 2: Response Synthesis
            elif "final response generator" in system_content.lower() or "findings:" in human_content or "Specialist agent findings:" in human_content:
                findings = ""
                lines = human_content.split("\n")
                in_findings = False
                for line in lines:
                    if "findings:" in line or "Specialist agent findings:" in line:
                        in_findings = True
                        continue
                    if in_findings:
                        findings += line + "\n"
                findings = findings.strip()

                # Detect language of findings to wrap appropriately
                findings_lang = self._detect_lang(findings)
                if not findings or "No specialist agent output" in findings:
                    defaults = {
                        "hindi": "नमस्ते! मैं आपका पर्सनल वॉयस एआई असिस्टेंट हूँ। आज मैं आपकी क्या मदद कर सकता हूँ?",
                        "bhojpuri": "प्रणाम! हम राउर पर्सनल आवाज एआई सहायक बानी। आज हम राउर कइसे मदद करीं?",
                        "marathi": "नमस्कार! मी तुमचा वैयक्तिक व्हॉइस एआय असिस्टंट आहे. आज मी तुम्हाला कशी मदत करू शकतो?",
                        "kannada": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ಧ್ವನಿ ಎഐ ಸಹಾಯಕ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
                        "telugu": "నమస్కారం! నేను మీ వ్యక్తిగత వాయిస్ ఏఐ అసిస్టెంట్ ని. ఈ రోజు మీకు ఎలా సహాయపడగలను?",
                        "tamil": "வணக்கம்! நான் உங்கள் தனிப்பட்ட குரல் AI உதவியாளர். இன்று நான் உங்களுக்கு எவ்வாறு உதవ முடியும்?",
                        "bengali": "নমস্কার! আমি আপনার ব্যক্তিগত ভয়েস এআই সহকারী। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
                        "odia": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କ ବ୍ୟକ୍ତିଗତ ଭଏସ୍ ଏଆଇ ସହକାରୀ। ଆଜି ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
                        "gujarati": "നമസ്ਤੇ! હું તમારો ପર્સനલ વોઇસ એઆઇ આસિસ્ટન્ટ છું. આજે હું તમને કેવી રીતે મદદ કરી શકું?",
                        "punjabi": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਨਿੱਜੀ ਵੌਇਸ ਏਆਈ ਸਹਾਇਕ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
                        "malayalam": "ഹലോ! ഞാൻ നിങ്ങളുടെ പേഴ്സണൽ വോയിസ് എഐ അസിസ്റ്റന്റ് ആണ്. ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?",
                        "haryanvi": "राम राम जी! मैं थारा पर्सनल वॉयस एआई असिस्टेंट हूँ। आज मैं थारी के मदद कर सकूँ हूँ?",
                        "awadhi": "प्रणाम! हम तुम्हार पर्सनल वॉयस एआई असिस्टेंट अही। आज हम तुम्हार का सहायता करी?",
                        "braj bhasha": "राधे राधे! मैं तिहारौ पर्सनल वॉयस एआई असिस्टेंट हूँ। आज मैं तिहारी कहा मदद करूँ?",
                        "marwari": "खम्मा घणी! मैं थारो खुद को वॉयस एआई असिस्टेंट हूँ। आज मैं थारी कांई मदद करूँ?",
                        "english": "Hello! I am Javis, your personal AI assistant. How can I help you today?"
                    }
                    findings = defaults.get(findings_lang, defaults["english"])
                
                if findings.startswith("###") or findings.startswith("🤖"):
                    response_text = findings
                else:
                    wrappers = {
                        "hindi": "🤖 [मॉक मोड] यहाँ मुझे आपके लिए क्या मिला है:\n\n{findings}\n\nक्या आप कुछ और जानना चाहते हैं?",
                        "bhojpuri": "🤖 [मॉक मोड] राउर खातिर हमके ई मिलल बा:\n\n{findings}\n\nराउर कुछ अउर जाने के बा?",
                        "marathi": "🤖 [मॉक मोड] तुमच्यासाठी मला काय आढळले ते येथे आहे:\n\n{findings}\n\nतुम्हाला आणखी काही जाणून घ्यायचे आहे का?",
                        "kannada": "🤖 [ಮಾക് ಮೋಡ್] ನಿਮಗಾಗಿ ನಾನು ಕಂಡुकೊಂಡಿದ್ದು ಇಲ್ಲಿದೆ:\n\n{findings}\n\nನೀವು ಇನ್ನೇನಾದರೂ ತಿಳಿಯಲು ಬಯਸುವಿರಾ?",
                        "telugu": "🤖 [माक मोड] నేను మీ కోసం కనుగొన్నది ఇక్కడ ఉంది:\n\n{findings}\n\nమీరు ఇంకేదైనా తెలుసుకోవాలనుకుంటున్నారా?",
                        "tamil": "🤖 [மாக் பயன்முறை] உங்களுக்காக நான் கண்டறிந்தது இதோ:\n\n{findings}\n\nநீங்கள் வேறு ఏదేனும் அறிய விரும்புகிறீர்களா?",
                        "bengali": "🤖 [মক মোড] আপনার জন্য আমি যা পেয়েছি তা এখানে রয়েছে:\n\n{findings}\n\nআপনি কি অন্য কিছু জানতে চান?",
                        "odia": "🤖 [ମକ୍ ମୋଡ୍] ଆପଣଙ୍କ ପାଇଁ ମୁଁ ଯାହା ପାଇଛି ତାହା ଏଠାରେ ଅଛି:\n\n{findings}\n\nଆପଣ ଆଉ କିଛି ଜାଣିବାକୁ ଚାହାଁନ୍ତି କି?",
                        "gujarati": "🤖 [મોક મોડ] તમારા માટે મને જે મળ્યું છે તે અહીં છે:\n\n{findings}\n\nશું તમે બીજું કંઈ જાણવા માંગો છો?",
                        "punjabi": "🤖 [ਮੌਕ ਮੋਡ] ਤੁਹਾਡੇ ਲਈ ਮੈਨੂੰ ਇਹ ਮਿਲਿਆ ਹੈ:\n\n{findings}\n\nਕੀ ਤੁਸੀਂ ਕੁਝ ਹੋਰ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
                        "malayalam": "🤖 [മോക്ക് മോഡ്] നിങ്ങളുടെ വിവരങ്ങൾ ഇതാ:\n\n{findings}\n\nനിങ്ങൾക്ക് മറ്റെന്തെങ്കിലും അറിയണമെന്നുണ്ടോ?",
                        "haryanvi": "🤖 [मॉक मोड] थारे खातर मन्ने यो मिल्या सै:\n\n{findings}\n\nਕੇ थारे कुछ और भी जाणना सै?",
                        "awadhi": "🤖 [मॉक मोड] तुम्हार बरे हमका ई मिला अहै:\n\n{findings}\n\nका तुम्हार कुछ अउर जाने क इच्छा अहै?",
                        "braj bhasha": "🤖 [मॉक मोड] तिहारे बरे मोय यह मिल्यौ है:\n\n{findings}\n\nका तुम कछु और जानिबौ चाहत हो?",
                        "marwari": "🤖 [मॉक मोड] थारे सारू म्हाने ओ मिल्यो है:\n\n{findings}\n\nकांई थाने और भी कांई जाणनो है?",
                        "english": "🤖 [Mock Mode] Here is what I found for you:\n\n{findings}\n\nIs there anything else you would like to know?"
                    }
                    wrapper = wrappers.get(findings_lang, wrappers["english"])
                    response_text = wrapper.format(findings=findings)

                return MockAIMessage(response_text)

            # Case 3: Memory Extraction
            elif "facts worth remembering" in system_content.lower() or "memory extraction" in system_content.lower() or "memory extraction" in human_content.lower() or "memory_extraction" in human_content.lower() or "extract any facts" in system_content.lower() or "extract any facts" in human_content.lower():
                return MockAIMessage("[]")

            # Case 4: Specialist agents / fallback
            else:
                query = human_content.strip()
                actual_query = query
                for line in query.split("\n"):
                    if "user question:" in line.lower():
                        actual_query = line.split(":", 1)[1].strip()
                        break
                    elif "user asked:" in line.lower():
                        actual_query = line.split(":", 1)[1].strip()
                        break
                actual_query = actual_query.strip("\"'")
                
                # Check specific agent triggers first
                if "coding mentor" in system_content.lower():
                    return MockAIMessage(self._get_structured_response("coding", lang=lang))
                
                # Default structured lookup
                structured_res = self._get_structured_response(actual_query, lang=lang)
                return MockAIMessage(structured_res)

        async def astream(self, messages, *args, **kwargs):
            response = await self.ainvoke(messages, *args, **kwargs)
            text = response.content
            
            # Yield chunks with a slight delay
            chunk_size = 10
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                yield MockAIMessageChunk(chunk)
                await asyncio.sleep(0.01)

        def invoke(self, *args, **kwargs):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.ainvoke(*args, **kwargs))

    # Pre-import and patch langchain_openai globally before other imports
    try:
        import langchain_openai
        langchain_openai.ChatOpenAI = MockChatOpenAI
        sys.modules['langchain_openai'].ChatOpenAI = MockChatOpenAI
    except ImportError:
        pass

from app.database import create_tables
from app.redis_client import get_redis, close_redis
from app.utils.logger import setup_logging, logger
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router
from app.api.memory import router as memory_router
from app.api.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging()
    logger.info("voice_agent_starting", environment=settings.environment)

    # Initialize database tables
    try:
        await create_tables()
        logger.info("database_tables_ready")

        # Seed default admin user if no users exist
        from app.database import AsyncSessionLocal
        from app.models.user import User
        from app.services.auth_service import get_password_hash
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).limit(1))
            if not result.scalar_one_or_none():
                admin_user = User(
                    email="admin@example.com",
                    username="admin",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Administrator",
                    is_active=True,
                    is_verified=True,
                    profile={}
                )
                session.add(admin_user)
                await session.commit()
                logger.info("default_admin_user_seeded", email="admin@example.com")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))

    # Initialize Redis
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))

    # Set OpenAI API key in env (for LangChain compatibility)
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()

    # Pre-compile LangGraph and warm up the LLM model to optimize response times
    try:
        from app.agents.graph import build_graph
        build_graph()
        logger.info("langgraph_precompiled_on_startup")

        # Send a brief background query to warm up the LLM (useful for loading local Ollama models)
        if not (settings.openai_api_key.startswith("mock-key") or "mock-key" in settings.openai_api_key):
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            import asyncio

            async def warmup_llm():
                try:
                    llm = ChatOpenAI(
                        model=settings.llm_model,
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url or None,
                        max_tokens=5,
                    )
                    await llm.ainvoke([HumanMessage(content="hi")])
                    logger.info("llm_model_warmed_up")
                except Exception as ex:
                    logger.warning("llm_warmup_failed", error=str(ex))

            asyncio.create_task(warmup_llm())
    except Exception as e:
        logger.warning("agent_pipeline_warmup_failed", error=str(e))

    logger.info("voice_agent_started", port=settings.backend_port)
    yield

    # Shutdown
    await close_redis()
    logger.info("voice_agent_stopped")


app = FastAPI(
    title="Personal Voice AI Agent",
    description="""
    A production-ready Personal Voice AI Agent with:
    - 🎙️ Speech-to-Text (OpenAI Whisper / Deepgram)
    - 🔊 Text-to-Speech (OpenAI TTS / ElevenLabs)
    - 🧠 LangGraph Multi-Agent Orchestration
    - 💾 4-Layer Memory System (Short-term, Long-term, Semantic, Episodic)
    - 🔧 Tool Calling (Web Search, Calculator, Weather, Email, Calendar)
    - 👤 10 Specialist Agents (Research, Coding, Learning, Productivity, Wellness, Career, Email, Planner)
    - 🔐 JWT Authentication
    - 📡 WebSocket Streaming
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ──────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
