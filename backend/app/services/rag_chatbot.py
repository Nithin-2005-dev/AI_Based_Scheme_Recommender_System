"""
RAG Chatbot Service with Eligibility Engine Integration.
Retrieval-Augmented Generation using scheme data as knowledge base.
Supports English, Telugu, Hindi with profile-aware personalized responses.
"""

import uuid
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from loguru import logger

from app.models.scheme import Scheme
from app.models.user import User
from app.models.notification import ChatHistory
from app.core.config import get_settings
from app.services.eligibility_rules import detect_language

settings = get_settings()

# ===== Trilingual support =====
SUPPORTED_CHAT_LANGUAGES = {
    "en": "English",
    "te": "తెలుగు",
    "hi": "हिन्दी",
}

# Intent detection keywords in all 3 languages
INTENT_KEYWORDS = {
    "eligibility_personal": {
        "en": ["am i eligible", "eligible for", "what schemes am i", "schemes i am eligible",
               "my eligibility", "can i apply", "which schemes for me", "what can i get",
               "show me schemes i am eligible", "schemes i qualify"],
        "te": ["నాకు అర్హత", "ఏ పథకాలకు అర్హత", "నాకు ఏ", "అర్హత ఉంది",
               "నేను అర్హుడిని", "నాకు వచ్చే", "పథకాలు చూపించు"],
        "hi": ["मैं पात्र", "किन योजनाओं के लिए पात्र", "मेरी पात्रता",
               "मैं किन", "मुझे कौन सी", "योजनाएं बताओ", "मेरे लिए योजनाएं"],
    },
    "eligibility_specific": {
        "en": ["eligible for pm", "eligible for pradhan", "eligible for national",
               "am i eligible for", "can i get"],
        "te": ["అర్హత ఉందా", "పథకానికి అర్హత"],
        "hi": ["के लिए पात्र हूँ", "योजना के लिए", "मिल सकता है"],
    },
    "not_eligible_reason": {
        "en": ["why am i not eligible", "why not eligible", "why can't i",
               "reason not eligible", "why ineligible"],
        "te": ["ఎందుకు అనర్హ", "ఎందుకు అర్హత లేదు"],
        "hi": ["क्यों पात्र नहीं", "अपात्र क्यों", "कारण बताओ"],
    },
    "eligibility_info": {
        "en": ["eligibility", "eligible", "qualify", "who can apply", "criteria"],
        "te": ["అర్హత", "ఎవరు దరఖాస్తు"],
        "hi": ["पात्रता", "योग्यता", "कौन आवेदन कर सकता"],
    },
    "benefits": {
        "en": ["benefit", "advantages", "what do i get", "money", "amount", "financial", "assistance"],
        "te": ["ప్రయోజనాలు", "లాభాలు", "ఎంత డబ్బు", "ఆర్థిక సహాయం"],
        "hi": ["लाभ", "फायदे", "कितना पैसा", "आर्थिक सहायता", "राशि"],
    },
    "documents": {
        "en": ["document", "papers", "required", "need to submit", "certificates"],
        "te": ["పత్రాలు", "డాక్యుమెంట్లు", "సర్టిఫికేట్లు", "కావలసిన పత్రాలు"],
        "hi": ["दस्तावेज़", "कागजात", "प्रमाण पत्र", "जरूरी कागज"],
    },
    "application": {
        "en": ["how to apply", "application", "apply", "process", "steps", "register"],
        "te": ["దరఖాస్తు ఎలా", "ఎలా అప్లై", "దరఖాస్తు ప్రక్రియ"],
        "hi": ["आवेदन कैसे करें", "अप्लाई कैसे", "प्रक्रिया", "रजिस्टर"],
    },
    "search": {
        "en": ["find", "search", "list", "show", "schemes for", "available"],
        "te": ["చూపించు", "వెతుకు", "జాబితా"],
        "hi": ["खोजो", "दिखाओ", "सूची", "बताओ"],
    },
}

# Response templates in all 3 languages
RESPONSE_TEMPLATES = {
    "en": {
        "eligible_header": "Based on your profile, you are **eligible** for the following schemes:",
        "not_eligible_header": "Based on your profile analysis, you are **not eligible** for this scheme.",
        "scheme_eligible": "✅ **{name}** — You are eligible! (Confidence: {confidence}%)",
        "matched": "✓ {criteria}",
        "failed": "✗ {criteria}",
        "no_eligible": "Based on your current profile, I couldn't find eligible schemes from the top results. Try completing your profile for better matches.",
        "specific_eligible": "✅ You are **eligible** for **{name}**!\n\n**Matched criteria:**",
        "specific_not_eligible": "❌ You are **not eligible** for **{name}**.\n\n**Reasons:**",
        "not_found": "I couldn't find a scheme matching '{name}'. Please check the scheme name.",
        "welcome": "Hello! 👋 I'm the GovScheme AI Assistant. I can help you with:\n\n• 🔍 Finding government schemes\n• ✅ Checking your eligibility\n• 📄 Required documents\n• 📝 How to apply\n• 🎁 Understanding benefits\n\nAsk me anything about Indian government schemes!",
        "no_results": "I couldn't find specific schemes matching your query. Try:\n\n1. Using different keywords\n2. Browse schemes by category\n3. Ask about eligibility, benefits, or application process",
        "source_note": "\n\n---\n*This information is from official government scheme documents. Please verify with the official website before applying.*",
    },
    "te": {
        "eligible_header": "మీ ప్రొఫైల్ ఆధారంగా, మీరు ఈ క్రింది పథకాలకు **అర్హులు**:",
        "not_eligible_header": "మీ ప్రొఫైల్ విశ్లేషణ ఆధారంగా, మీరు ఈ పథకానికి **అనర్హులు**.",
        "scheme_eligible": "✅ **{name}** — మీరు అర్హులు! (నమ్మకం: {confidence}%)",
        "matched": "✓ {criteria}",
        "failed": "✗ {criteria}",
        "no_eligible": "మీ ప్రస్తుత ప్రొఫైల్ ఆధారంగా, అర్హత ఉన్న పథకాలు కనుగొనబడలేదు. మెరుగైన ఫలితాల కోసం మీ ప్రొఫైల్ పూర్తి చేయండి.",
        "specific_eligible": "✅ మీరు **{name}** కు **అర్హులు**!\n\n**సరిపోలిన అర్హతలు:**",
        "specific_not_eligible": "❌ మీరు **{name}** కు **అనర్హులు**.\n\n**కారణాలు:**",
        "not_found": "'{name}' అనే పథకం కనుగొనబడలేదు. దయచేసి పథకం పేరు తనిఖీ చేయండి.",
        "welcome": "నమస్కారం! 👋 నేను GovScheme AI సహాయకుడిని. నేను మీకు ఈ విషయాలలో సహాయం చేయగలను:\n\n• 🔍 ప్రభుత్వ పథకాలు కనుగొనడం\n• ✅ మీ అర్హత తనిఖీ\n• 📄 అవసరమైన పత్రాలు\n• 📝 దరఖాస్తు ఎలా చేయాలి\n• 🎁 ప్రయోజనాలు\n\nప్రభుత్వ పథకాల గురించి ఏదైనా అడగండి!",
        "no_results": "మీ ప్రశ్నకు సరిపోయే పథకాలు కనుగొనబడలేదు. వేరే పదాలతో ప్రయత్నించండి.",
        "source_note": "\n\n---\n*ఈ సమాచారం అధికారిక ప్రభుత్వ పత్రాల నుండి. దరఖాస్తు చేయడానికి ముందు అధికారిక వెబ్‌సైట్‌లో ధృవీకరించండి.*",
    },
    "hi": {
        "eligible_header": "आपकी प्रोफ़ाइल के आधार पर, आप निम्नलिखित योजनाओं के लिए **पात्र** हैं:",
        "not_eligible_header": "आपकी प्रोफ़ाइल विश्लेषण के आधार पर, आप इस योजना के लिए **अपात्र** हैं.",
        "scheme_eligible": "✅ **{name}** — आप पात्र हैं! (विश्वास: {confidence}%)",
        "matched": "✓ {criteria}",
        "failed": "✗ {criteria}",
        "no_eligible": "आपकी वर्तमान प्रोफ़ाइल के आधार पर, पात्र योजनाएं नहीं मिलीं। बेहतर परिणामों के लिए अपनी प्रोफ़ाइल पूरी करें।",
        "specific_eligible": "✅ आप **{name}** के लिए **पात्र** हैं!\n\n**मिलान मापदंड:**",
        "specific_not_eligible": "❌ आप **{name}** के लिए **अपात्र** हैं.\n\n**कारण:**",
        "not_found": "'{name}' नाम की योजना नहीं मिली। कृपया योजना का नाम जाँचें।",
        "welcome": "नमस्ते! 👋 मैं GovScheme AI सहायक हूँ। मैं इन विषयों में आपकी मदद कर सकता हूँ:\n\n• 🔍 सरकारी योजनाएं खोजना\n• ✅ आपकी पात्रता जांचना\n• 📄 आवश्यक दस्तावेज़\n• 📝 आवेदन कैसे करें\n• 🎁 लाभ समझना\n\nसरकारी योजनाओं के बारे में कुछ भी पूछें!",
        "no_results": "आपके प्रश्न से मेल खाने वाली योजनाएं नहीं मिलीं। अलग शब्दों से प्रयास करें।",
        "source_note": "\n\n---\n*यह जानकारी आधिकारिक सरकारी दस्तावेज़ों से है। आवेदन करने से पहले आधिकारिक वेबसाइट पर सत्यापित करें।*",
    },
}


class RAGChatbot:
    """
    RAG-based chatbot that answers questions using government scheme data.
    Integrates with EligibilityChecker for personalized, deterministic responses.
    Supports English, Telugu, Hindi.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ask(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None,
        language: str = "en",
        user: Optional[User] = None,
    ) -> dict:
        """
        Process a user question and return an answer with citations.

        Architecture:
        User → Intent Detection (en/te/hi) →
          If eligibility question → EligibilityChecker → Deterministic result →
            Format response → Translate to user's language → Return
          If general question → Existing RAG pipeline → Translate → Return
        """
        # Dynamically detect language from the user question
        detected_lang = detect_language(message)
        if detected_lang in ("te", "hi"):
            language = detected_lang
        elif language not in SUPPORTED_CHAT_LANGUAGES:
            language = "en"

        if not session_id:
            session_id = str(uuid.uuid4())

        # Get user object if not provided
        if user is None:
            from app.models.user import User as UserModel
            result = await self.db.execute(select(UserModel).where(UserModel.id == user_id))
            user = result.scalar_one_or_none()

        # Save user message
        user_chat = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role="user",
            message=message,
        )
        self.db.add(user_chat)

        # Step 1: Detect intent (multilingual)
        intent = self._detect_intent_multilingual(message, language)

        # Step 2: Route based on intent
        if intent == "eligibility_personal" and user:
            answer, citations, confidence = await self._handle_personal_eligibility(user, language)
        elif intent == "eligibility_specific" and user:
            scheme_name = self._extract_scheme_name(message)
            answer, citations, confidence = await self._handle_specific_eligibility(user, scheme_name, language)
        elif intent == "not_eligible_reason" and user:
            scheme_name = self._extract_scheme_name(message)
            answer, citations, confidence = await self._handle_not_eligible_reason(user, scheme_name, language)
        else:
            # Standard RAG pipeline
            keywords = self._extract_keywords(message)
            relevant_schemes = await self._retrieve_relevant_schemes(keywords, intent)

            if not relevant_schemes:
                templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])
                answer = templates["no_results"]
                citations = []
                confidence = 0.2
            else:
                answer, citations, confidence = self._generate_answer(
                    message, intent, relevant_schemes, language
                )

        # Save assistant response
        assistant_chat = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            message=answer,
            citations=[c["scheme_name"] for c in citations] if citations else [],
            confidence=confidence,
        )
        self.db.add(assistant_chat)

        return {
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "session_id": session_id,
            "source_chunks": [],
            "language": language,
        }

    def _detect_intent_multilingual(self, message: str, language: str) -> str:
        """Detect user's intent from their message in any of the 3 languages."""
        msg_lower = message.lower()

        # Check intents in priority order
        priority_order = [
            "eligibility_personal",
            "not_eligible_reason",
            "eligibility_specific",
            "eligibility_info",
            "benefits",
            "documents",
            "application",
            "search",
        ]

        for intent_name in priority_order:
            keywords_map = INTENT_KEYWORDS.get(intent_name, {})
            # Check all languages (user might mix languages)
            for lang, keywords in keywords_map.items():
                for kw in keywords:
                    if kw in msg_lower:
                        return intent_name

        return "general"

    def _extract_scheme_name(self, message: str) -> str:
        """Extract scheme name from user message."""
        # Common patterns
        patterns = [
            r'eligible for\s+(.+?)[\?\.\!]?$',
            r'not eligible for\s+(.+?)[\?\.\!]?$',
            r'eligibility for\s+(.+?)[\?\.\!]?$',
            r'about\s+(.+?)[\?\.\!]?$',
            r'(?:pm|pradhan mantri|national)\s+\w+(?:\s+\w+)*',
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1) if match.lastindex else match.group(0)
                return name.strip().rstrip('?!.')

        # Fallback: extract after "for" keyword
        for_match = re.search(r'for\s+(.+?)[\?\.\!]?$', message, re.IGNORECASE)
        if for_match:
            return for_match.group(1).strip().rstrip('?!.')

        # Last resort: use the whole message minus common question words
        cleaned = re.sub(
            r'\b(what|why|how|am|i|is|can|the|a|an|my|not|eligible|eligibility|for|show|tell|me|about|schemes|scheme)\b',
            '', message, flags=re.IGNORECASE
        ).strip()
        return cleaned if cleaned else message

    async def _handle_personal_eligibility(self, user: User, language: str) -> tuple:
        """Handle 'What schemes am I eligible for?' using deterministic engine."""
        from app.services.eligibility_checker import EligibilityChecker

        templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])
        checker = EligibilityChecker(self.db)
        eligible_schemes = await checker.get_eligible_schemes_for_chatbot(user, limit=10)

        citations = []

        if not eligible_schemes:
            return templates["no_eligible"], [], 0.7

        parts = [templates["eligible_header"], ""]

        for i, scheme in enumerate(eligible_schemes[:10], 1):
            confidence_pct = round(scheme["confidence"] * 100)
            parts.append(templates["scheme_eligible"].format(
                name=scheme["scheme_name"],
                confidence=confidence_pct,
            ))

            if scheme["matched_criteria"]:
                for criteria in scheme["matched_criteria"][:3]:
                    parts.append(f"  {templates['matched'].format(criteria=criteria)}")

            parts.append("")

            citations.append({
                "scheme_name": scheme["scheme_name"],
                "slug": scheme.get("slug", ""),
                "relevance": round(1.0 - (i * 0.08), 2),
            })

        parts.append(templates["source_note"])
        answer = "\n".join(parts)
        return answer, citations, 0.9

    async def _handle_specific_eligibility(self, user: User, scheme_name: str, language: str) -> tuple:
        """Handle 'Am I eligible for PM Kisan?' using deterministic engine."""
        from app.services.eligibility_checker import EligibilityChecker

        templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])
        checker = EligibilityChecker(self.db)
        result = await checker.check_scheme_for_chatbot(user, scheme_name)

        if not result.get("found"):
            return templates["not_found"].format(name=scheme_name), [], 0.5

        citations = [{
            "scheme_name": result["scheme_name"],
            "slug": result.get("slug", ""),
            "relevance": 1.0,
        }]

        parts = []
        if result["is_eligible"]:
            parts.append(templates["specific_eligible"].format(name=result["scheme_name"]))
            for criteria in result["matched_criteria"]:
                parts.append(f"  {templates['matched'].format(criteria=criteria)}")
        else:
            parts.append(templates["specific_not_eligible"].format(name=result["scheme_name"]))
            for criteria in result["failed_criteria"]:
                parts.append(f"  {templates['failed'].format(criteria=criteria)}")

        if result.get("missing_documents"):
            if language == "te":
                parts.append("\n📄 **అవసరమైన పత్రాలు:**")
            elif language == "hi":
                parts.append("\n📄 **आवश्यक दस्तावेज़:**")
            else:
                parts.append("\n📄 **Missing documents:**")
            for doc in result["missing_documents"]:
                parts.append(f"  • {doc}")

        parts.append(templates["source_note"])
        answer = "\n".join(parts)
        return answer, citations, 0.92

    async def _handle_not_eligible_reason(self, user: User, scheme_name: str, language: str) -> tuple:
        """Handle 'Why am I not eligible for PMAY?' using deterministic engine."""
        from app.services.eligibility_checker import EligibilityChecker

        templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])
        checker = EligibilityChecker(self.db)
        result = await checker.check_scheme_for_chatbot(user, scheme_name)

        if not result.get("found"):
            return templates["not_found"].format(name=scheme_name), [], 0.5

        citations = [{
            "scheme_name": result["scheme_name"],
            "slug": result.get("slug", ""),
            "relevance": 1.0,
        }]

        parts = []
        if result["is_eligible"]:
            if language == "te":
                parts.append(f"మీరు **{result['scheme_name']}** కు అర్హులు! మీ ప్రొఫైల్ అన్ని అవసరాలను తీరుస్తుంది.")
            elif language == "hi":
                parts.append(f"आप **{result['scheme_name']}** के लिए पात्र हैं! आपकी प्रोफ़ाइल सभी आवश्यकताओं को पूरा करती है।")
            else:
                parts.append(f"Actually, you **are eligible** for **{result['scheme_name']}**! Your profile meets the requirements.")
            if result["matched_criteria"]:
                parts.append("")
                for criteria in result["matched_criteria"]:
                    parts.append(f"  {templates['matched'].format(criteria=criteria)}")
        else:
            parts.append(templates["specific_not_eligible"].format(name=result["scheme_name"]))
            if result["failed_criteria"]:
                for criteria in result["failed_criteria"]:
                    parts.append(f"  {templates['failed'].format(criteria=criteria)}")
            if result["matched_criteria"]:
                parts.append("")
                if language == "te":
                    parts.append("**సరిపోలిన అర్హతలు:**")
                elif language == "hi":
                    parts.append("**मिलान मापदंड:**")
                else:
                    parts.append("**However, you do meet these criteria:**")
                for criteria in result["matched_criteria"]:
                    parts.append(f"  {templates['matched'].format(criteria=criteria)}")

        parts.append(templates["source_note"])
        answer = "\n".join(parts)
        return answer, citations, 0.92

    def _extract_keywords(self, message: str) -> list[str]:
        """Extract search keywords from user message (multilingual)."""
        stop_words = {
            "what", "is", "are", "how", "can", "i", "do", "the", "a", "an",
            "to", "for", "of", "in", "and", "or", "my", "me", "am", "this",
            "that", "it", "be", "have", "has", "was", "were", "been", "will",
            "would", "could", "should", "may", "might", "shall", "tell",
            "about", "please", "help", "need", "want", "get", "know",
            "which", "who", "where", "when", "why", "does", "did",
            "show", "find", "list",
        }

        words = re.findall(r'\b\w+\b', message.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Map Telugu and Hindi words to English concept keywords
        topical_map = {
            # Students & Education
            "విద్యార్థి": ["student", "scholarship", "education"],
            "విద్యార్థులకు": ["student", "scholarship", "education"],
            "స్కాలర్‌షిప్": ["scholarship"],
            "చదువు": ["education", "student"],
            "छात्र": ["student", "scholarship", "education"],
            "छात्रों": ["student", "scholarship", "education"],
            "विद्यार्थी": ["student", "scholarship", "education"],
            "छात्रवृत्ति": ["scholarship"],
            "शिक्षा": ["education", "scholarship"],
            # Farmers & Agriculture
            "రైతు": ["farmer", "kisan", "agriculture"],
            "రైతులకు": ["farmer", "kisan", "agriculture"],
            "వ్యవసాయం": ["agriculture", "farmer"],
            "వ్యవసాయ": ["agriculture", "farmer"],
            "किसान": ["farmer", "kisan", "agriculture"],
            "किसानों": ["farmer", "kisan", "agriculture"],
            "कृषि": ["agriculture", "farmer"],
            # Women & Girls
            "మహిళ": ["women", "woman", "female"],
            "మహిళలకు": ["women", "woman", "female"],
            "స్త్రీ": ["women", "female"],
            "महिला": ["women", "woman", "female"],
            "महिलाओं": ["women", "female"],
            "लड़की": ["girl", "female"],
            # Health
            "ఆరోగ్య": ["health", "medical", "ayushman"],
            "వైద్య": ["medical", "health"],
            "स्वास्थ्य": ["health", "medical", "ayushman"],
            "इलाज": ["treatment", "health"],
            # Housing
            "గృహ": ["housing", "shelter", "pmay"],
            "ఇల్లు": ["housing", "shelter"],
            "ఆవాస్": ["housing", "pmay"],
            "आवास": ["housing", "shelter", "pmay"],
            "घर": ["housing", "shelter"],
            "मकान": ["housing", "shelter"],
            # Pension & Senior Citizen
            "వృద్ధాప్య": ["old age", "pension", "senior citizen"],
            "పెన్షన్": ["pension"],
            "वृद्धावस्था": ["old age", "pension", "senior citizen"],
            "पेंशन": ["pension"],
            # Business & Loans
            "వ్యాపార": ["business", "msme", "mudra"],
            "రుణం": ["loan", "credit", "mudra"],
            "రుణాలు": ["loan", "mudra"],
            "व्यापार": ["business", "msme", "mudra"],
            "व्यवसाय": ["business", "msme"],
            "ऋण": ["loan", "mudra"],
        }
        for term, mapped in topical_map.items():
            if term in message:
                keywords.extend(mapped)

        # Also handle Telugu/Hindi by keeping non-ASCII words
        non_ascii = re.findall(r'[^\x00-\x7F]+', message)
        keywords.extend(non_ascii)

        return list(dict.fromkeys(keywords))

    async def _retrieve_relevant_schemes(
        self, keywords: list[str], intent: str, limit: int = 5
    ) -> list[Scheme]:
        """Retrieve schemes relevant to the user's query."""
        if not keywords:
            result = await self.db.execute(
                select(Scheme)
                .where(Scheme.is_active == True)
                .order_by(Scheme.view_count.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        conditions = []
        for kw in keywords:
            pattern = f"%{kw}%"
            conditions.append(Scheme.scheme_name.ilike(pattern))
            conditions.append(Scheme.details.ilike(pattern))
            conditions.append(Scheme.eligibility.ilike(pattern))
            conditions.append(Scheme.benefits.ilike(pattern))
            conditions.append(Scheme.scheme_category.ilike(pattern))
            conditions.append(Scheme.documents_required.ilike(pattern))

        result = await self.db.execute(
            select(Scheme)
            .where(Scheme.is_active == True, or_(*conditions))
            .limit(limit)
        )
        return list(result.scalars().all())

    def _generate_answer(
        self,
        question: str,
        intent: str,
        schemes: list[Scheme],
        language: str = "en",
    ) -> tuple[str, list[dict], float]:
        """Generate a comprehensive answer from retrieved scheme data."""
        citations = []
        answer_parts = []
        confidence = 0.0
        templates = RESPONSE_TEMPLATES.get(language, RESPONSE_TEMPLATES["en"])

        if intent in ("eligibility_info", "eligibility"):
            if language == "te":
                answer_parts.append("అధికారిక పథకం పత్రాల ఆధారంగా, అర్హత ప్రమాణాలు:\n")
            elif language == "hi":
                answer_parts.append("आधिकारिक योजना दस्तावेज़ों के आधार पर, पात्रता मानदंड:\n")
            else:
                answer_parts.append("Based on official scheme documents, here are the eligibility criteria:\n")
            for i, scheme in enumerate(schemes[:3], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}**")
                if scheme.eligibility:
                    answer_parts.append(f"{scheme.eligibility[:600]}")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.2), 2),
                })
            confidence = 0.85

        elif intent == "benefits":
            if language == "te":
                answer_parts.append("ఈ పథకాల ద్వారా అందించే ప్రయోజనాలు:\n")
            elif language == "hi":
                answer_parts.append("इन योजनाओं के तहत प्रदान किए जाने वाले लाभ:\n")
            else:
                answer_parts.append("Here are the benefits provided under these schemes:\n")
            for i, scheme in enumerate(schemes[:3], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}**")
                if scheme.benefits:
                    answer_parts.append(f"{scheme.benefits[:600]}")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.2), 2),
                })
            confidence = 0.85

        elif intent == "documents":
            if language == "te":
                answer_parts.append("అవసరమైన పత్రాలు:\n")
            elif language == "hi":
                answer_parts.append("आवश्यक दस्तावेज़:\n")
            else:
                answer_parts.append("The following documents are required:\n")
            for i, scheme in enumerate(schemes[:3], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}**")
                if scheme.documents_required:
                    answer_parts.append(f"{scheme.documents_required[:600]}")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.2), 2),
                })
            confidence = 0.9

        elif intent == "application":
            if language == "te":
                answer_parts.append("దరఖాస్తు ప్రక్రియ:\n")
            elif language == "hi":
                answer_parts.append("आवेदन प्रक्रिया:\n")
            else:
                answer_parts.append("Here's how to apply:\n")
            for i, scheme in enumerate(schemes[:3], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}**")
                if scheme.application_process:
                    answer_parts.append(f"{scheme.application_process[:600]}")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.2), 2),
                })
            confidence = 0.85

        elif intent == "search":
            if language == "te":
                answer_parts.append(f"{len(schemes)} సంబంధిత పథకాలు కనుగొనబడ్డాయి:\n")
            elif language == "hi":
                answer_parts.append(f"{len(schemes)} संबंधित योजनाएं मिलीं:\n")
            else:
                answer_parts.append(f"I found {len(schemes)} relevant scheme(s):\n")
            for i, scheme in enumerate(schemes[:5], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}** ({scheme.level})")
                if scheme.details:
                    answer_parts.append(f"   {scheme.details[:200]}...")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.15), 2),
                })
            confidence = 0.8

        else:
            if language == "te":
                answer_parts.append("మీ ప్రశ్నకు సంబంధించిన సమాచారం:\n")
            elif language == "hi":
                answer_parts.append("आपके प्रश्न से संबंधित जानकारी:\n")
            else:
                answer_parts.append("Here's what I found related to your question:\n")
            for i, scheme in enumerate(schemes[:3], 1):
                answer_parts.append(f"**{i}. {scheme.scheme_name}** ({scheme.level})")
                if scheme.details:
                    answer_parts.append(f"   {scheme.details[:300]}")
                if scheme.benefits:
                    if language == "te":
                        answer_parts.append(f"   **ప్రయోజనాలు:** {scheme.benefits[:200]}")
                    elif language == "hi":
                        answer_parts.append(f"   **लाभ:** {scheme.benefits[:200]}")
                    else:
                        answer_parts.append(f"   **Benefits:** {scheme.benefits[:200]}")
                answer_parts.append("")
                citations.append({
                    "scheme_name": scheme.scheme_name,
                    "slug": scheme.slug,
                    "relevance": round(1.0 - (i * 0.2), 2),
                })
            confidence = 0.7

        answer_parts.append(templates["source_note"])
        return "\n".join(answer_parts), citations, confidence

    async def get_chat_history(
        self, user_id: int, session_id: str
    ) -> list[dict]:
        """Get chat history for a session."""
        result = await self.db.execute(
            select(ChatHistory)
            .where(
                ChatHistory.user_id == user_id,
                ChatHistory.session_id == session_id,
            )
            .order_by(ChatHistory.created_at.asc())
        )
        messages = result.scalars().all()

        return [
            {
                "role": m.role,
                "message": m.message,
                "citations": m.citations,
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
