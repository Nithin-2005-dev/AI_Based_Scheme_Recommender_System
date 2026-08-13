"""
Translation Service for multilingual support.
Supports 10 Indian languages with built-in UI dictionary + Google Translate fallback.
"""

from typing import Optional
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "mr": "मराठी",
    "bn": "বাংলা",
    "gu": "ગુજરાતી",
    "pa": "ਪੰਜਾਬੀ",
}

# Built-in translation dictionary for common UI strings
UI_TRANSLATIONS = {
    "hi": {
        "home": "होम", "search": "खोजें", "schemes": "योजनाएं",
        "profile": "प्रोफ़ाइल", "login": "लॉगिन", "signup": "साइन अप",
        "eligibility": "पात्रता", "benefits": "लाभ", "documents": "दस्तावेज़",
        "apply": "आवेदन करें", "notifications": "सूचनाएं", "dashboard": "डैशबोर्ड",
        "recommendations": "सिफारिशें", "chatbot": "चैटबॉट", "settings": "सेटिंग्स",
        "logout": "लॉग आउट", "central": "केंद्रीय", "state": "राज्य",
        "category": "श्रेणी", "income": "आय", "age": "आयु", "gender": "लिंग",
        "occupation": "व्यवसाय", "education": "शिक्षा", "name": "नाम",
        "email": "ईमेल", "password": "पासवर्ड", "submit": "जमा करें",
        "save": "सहेजें", "cancel": "रद्द करें", "delete": "हटाएं",
        "edit": "संपादित करें", "view": "देखें", "back": "वापस",
        "next": "अगला", "previous": "पिछला", "loading": "लोड हो रहा है",
        "no_results": "कोई परिणाम नहीं", "welcome": "स्वागत है",
        "eligible": "पात्र", "not_eligible": "अपात्र",
        "partially_eligible": "आंशिक रूप से पात्र",
        "deadline": "अंतिम तिथि", "application_process": "आवेदन प्रक्रिया",
        "required_documents": "आवश्यक दस्तावेज़",
        "scheme_details": "योजना विवरण", "filter": "फ़िल्टर",
        "all": "सभी", "farmer": "किसान", "student": "छात्र",
        "women": "महिला", "senior_citizen": "वरिष्ठ नागरिक",
        "disabled": "दिव्यांग", "business_owner": "व्यवसाय स्वामी",
    },
    "te": {
        "home": "హోమ్", "search": "శోధించు", "schemes": "పథకాలు",
        "profile": "ప్రొఫైల్", "login": "లాగిన్", "signup": "సైన్ అప్",
        "eligibility": "అర్హత", "benefits": "ప్రయోజనాలు", "documents": "పత్రాలు",
        "apply": "దరఖాస్తు చేయండి", "notifications": "నోటిఫికేషన్‌లు",
        "dashboard": "డాష్‌బోర్డ్", "recommendations": "సిఫార్సులు",
        "chatbot": "చాట్‌బాట్", "settings": "సెట్టింగ్‌లు", "logout": "లాగ్ అవుట్",
        "central": "కేంద్ర", "state": "రాష్ట్ర", "category": "వర్గం",
        "income": "ఆదాయం", "age": "వయస్సు", "gender": "లింగం",
        "occupation": "వృత్తి", "education": "విద్య", "name": "పేరు",
        "eligible": "అర్హులు", "not_eligible": "అనర్హులు",
        "deadline": "గడువు", "all": "అన్ని",
    },
    "ta": {
        "home": "முகப்பு", "search": "தேடு", "schemes": "திட்டங்கள்",
        "profile": "சுயவிவரம்", "login": "உள்நுழைவு", "signup": "பதிவு",
        "eligibility": "தகுதி", "benefits": "நன்மைகள்", "documents": "ஆவணங்கள்",
        "apply": "விண்ணப்பிக்க", "notifications": "அறிவிப்புகள்",
        "dashboard": "டாஷ்போர்டு", "recommendations": "பரிந்துரைகள்",
        "eligible": "தகுதியானவர்", "not_eligible": "தகுதியற்றவர்",
        "deadline": "காலக்கெடு", "all": "அனைத்தும்",
    },
    "kn": {
        "home": "ಮುಖಪುಟ", "search": "ಹುಡುಕು", "schemes": "ಯೋಜನೆಗಳು",
        "profile": "ಪ್ರೊಫೈಲ್", "login": "ಲಾಗಿನ್", "signup": "ಸೈನ್ ಅಪ್",
        "eligibility": "ಅರ್ಹತೆ", "benefits": "ಪ್ರಯೋಜನಗಳು", "documents": "ದಾಖಲೆಗಳು",
        "apply": "ಅರ್ಜಿ ಸಲ್ಲಿಸಿ", "notifications": "ಅಧಿಸೂಚನೆಗಳು",
        "eligible": "ಅರ್ಹ", "not_eligible": "ಅನರ್ಹ", "all": "ಎಲ್ಲಾ",
    },
    "ml": {
        "home": "ഹോം", "search": "തിരയുക", "schemes": "പദ്ധതികൾ",
        "profile": "പ്രൊഫൈൽ", "login": "ലോഗിൻ", "signup": "സൈൻ അപ്",
        "eligibility": "യോഗ്യത", "benefits": "ആനുകൂല്യങ്ങൾ", "documents": "രേഖകൾ",
        "apply": "അപേക്ഷിക്കുക", "eligible": "യോഗ്യൻ", "all": "എല്ലാം",
    },
    "mr": {
        "home": "मुखपृष्ठ", "search": "शोधा", "schemes": "योजना",
        "profile": "प्रोफाइल", "login": "लॉगिन", "signup": "साइन अप",
        "eligibility": "पात्रता", "benefits": "फायदे", "documents": "कागदपत्रे",
        "apply": "अर्ज करा", "eligible": "पात्र", "all": "सर्व",
    },
    "bn": {
        "home": "হোম", "search": "অনুসন্ধান", "schemes": "প্রকল্প",
        "profile": "প্রোফাইল", "login": "লগইন", "signup": "সাইন আপ",
        "eligibility": "যোগ্যতা", "benefits": "সুবিধা", "documents": "নথি",
        "apply": "আবেদন করুন", "eligible": "যোগ্য", "all": "সমস্ত",
    },
    "gu": {
        "home": "હોમ", "search": "શોધો", "schemes": "યોજનાઓ",
        "profile": "પ્રોફાઇલ", "login": "લોગિન", "signup": "સાઇન અપ",
        "eligibility": "પાત્રતા", "benefits": "લાભો", "documents": "દસ્તાવેજો",
        "apply": "અરજી કરો", "eligible": "પાત્ર", "all": "બધા",
    },
    "pa": {
        "home": "ਘਰ", "search": "ਖੋਜੋ", "schemes": "ਯੋਜਨਾਵਾਂ",
        "profile": "ਪ੍ਰੋਫ਼ਾਈਲ", "login": "ਲੌਗਇਨ", "signup": "ਸਾਈਨ ਅੱਪ",
        "eligibility": "ਯੋਗਤਾ", "benefits": "ਲਾਭ", "documents": "ਦਸਤਾਵੇਜ਼",
        "apply": "ਅਰਜ਼ੀ ਦਿਓ", "eligible": "ਯੋਗ", "all": "ਸਾਰੇ",
    },
}


class TranslationService:
    """Multilingual translation service."""

    def __init__(self):
        self._cache: dict[str, str] = {}

    def get_supported_languages(self) -> dict[str, str]:
        """Return all supported languages."""
        return SUPPORTED_LANGUAGES

    def get_ui_translations(self, language: str) -> dict[str, str]:
        """Get all UI string translations for a language."""
        if language == "en":
            return {}  # English is the default
        return UI_TRANSLATIONS.get(language, {})

    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
    ) -> dict:
        """Translate text to target language."""
        if target_language == source_language:
            return {
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "confidence": 1.0,
            }

        # Check cache
        cache_key = f"{source_language}:{target_language}:{text[:100]}"
        if cache_key in self._cache:
            return {
                "translated_text": self._cache[cache_key],
                "source_language": source_language,
                "target_language": target_language,
                "confidence": 0.95,
            }

        # Try Google Translate API if configured
        if settings.GOOGLE_TRANSLATE_API_KEY:
            try:
                translated = await self._google_translate(text, target_language, source_language)
                self._cache[cache_key] = translated
                return {
                    "translated_text": translated,
                    "source_language": source_language,
                    "target_language": target_language,
                    "confidence": 0.95,
                }
            except Exception as e:
                logger.error(f"Google Translate error: {e}")

        # Fallback: return original with note
        return {
            "translated_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "confidence": 0.0,
            "note": "Translation API not configured. Displaying original text.",
        }

    async def _google_translate(
        self, text: str, target: str, source: str
    ) -> str:
        """Use Google Translate API."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": settings.GOOGLE_TRANSLATE_API_KEY},
                json={
                    "q": text,
                    "target": target,
                    "source": source,
                    "format": "text",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["translations"][0]["translatedText"]


# Singleton
translation_service = TranslationService()
