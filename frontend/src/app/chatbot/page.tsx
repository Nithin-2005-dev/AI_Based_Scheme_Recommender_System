"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import Navbar from "@/components/Navbar";
import { useLanguage } from "@/context/LanguageContext";
import { SupportedLanguage } from "@/locales";

/* ===================================================================
 * Types
 * =================================================================*/
interface ChatMessage {
  role: "user" | "assistant";
  message: string;
  citations?: { scheme_name: string; slug: string; relevance: number }[];
  confidence?: number;
  source?: "text" | "voice";
}

type VoiceState =
  | "idle"
  | "listening"
  | "processing"
  | "transcribing"
  | "sending"
  | "responding"
  | "speaking"
  | "error";

/* ===================================================================
 * Constants
 * =================================================================*/
const LANGUAGES = [
  { code: "en", name: "English", flag: "🇬🇧", sttLang: "en-IN", ttsLang: "en-IN" },
  { code: "te", name: "తెలుగు", flag: "🇮🇳", sttLang: "te-IN", ttsLang: "te-IN" },
  { code: "hi", name: "हिन्दी", flag: "🇮🇳", sttLang: "hi-IN", ttsLang: "hi-IN" },
];

const WELCOME_MESSAGES: Record<string, string> = {
  en: "Hello! 👋 I'm the GovScheme AI Assistant. I can help you with:\n\n• 🔍 Finding government schemes\n• ✅ Checking your eligibility\n• 📄 Required documents\n• 📝 How to apply\n• 🎁 Understanding benefits\n\nI have access to your profile, so I can give you personalized answers!\n\nAsk me anything — by typing or using the 🎤 microphone!",
  te: "నమస్కారం! 👋 నేను GovScheme AI సహాయకుడిని. నేను మీకు ఈ విషయాలలో సహాయం చేయగలను:\n\n• 🔍 ప్రభుత్వ పథకాలు కనుగొనడం\n• ✅ మీ అర్హత తనిఖీ\n• 📄 అవసరమైన పత్రాలు\n• 📝 దరఖాస్తు ఎలా చేయాలి\n• 🎁 ప్రయోజనాలు\n\nమీ ప్రొఫైల్ ఆధారంగా వ్యక్తిగత సమాధానాలు ఇవ్వగలను!\n\nటైప్ చేయండి లేదా 🎤 మైక్రోఫోన్ ఉపయోగించండి!",
  hi: "नमस्ते! 👋 मैं GovScheme AI सहायक हूँ। मैं इन विषयों में आपकी मदद कर सकता हूँ:\n\n• 🔍 सरकारी योजनाएं खोजना\n• ✅ आपकी पात्रता जांचना\n• 📄 आवश्यक दस्तावेज़\n• 📝 आवेदन कैसे करें\n• 🎁 लाभ समझना\n\nआपकी प्रोफ़ाइल के आधार पर व्यक्तिगत उत्तर दे सकता हूँ!\n\nटाइप करें या 🎤 माइक्रोफ़ोन का उपयोग करें!",
};

const QUICK_QUESTIONS: Record<string, string[]> = {
  en: [
    "What schemes am I eligible for?",
    "Am I eligible for PM Kisan?",
    "Show me education scholarships",
    "How to apply for PMAY?",
    "What documents do I need?",
  ],
  te: [
    "నాకు ఏ పథకాలకు అర్హత ఉంది?",
    "PM కిసాన్ కు నాకు అర్హత ఉందా?",
    "విద్యా స్కాలర్‌షిప్‌లు చూపించండి",
    "PMAY కి ఎలా దరఖాస్తు చేయాలి?",
    "నాకు ఏ పత్రాలు కావాలి?",
  ],
  hi: [
    "मैं किन योजनाओं के लिए पात्र हूँ?",
    "क्या मैं PM किसान के लिए पात्र हूँ?",
    "शिक्षा छात्रवृत्ति दिखाओ",
    "PMAY के लिए कैसे आवेदन करें?",
    "मुझे कौन से दस्तावेज चाहिए?",
  ],
};

const STATUS_LABELS: Record<string, Record<VoiceState, string>> = {
  en: {
    idle: "Tap to speak",
    listening: "Listening...",
    processing: "Processing...",
    transcribing: "Transcribing...",
    sending: "Sending...",
    responding: "Thinking...",
    speaking: "Speaking...",
    error: "Error",
  },
  te: {
    idle: "మాట్లాడటానికి నొక్కండి",
    listening: "వింటోంది...",
    processing: "ప్రాసెస్ చేస్తోంది...",
    transcribing: "రాస్తోంది...",
    sending: "పంపుతోంది...",
    responding: "ఆలోచిస్తోంది...",
    speaking: "చెబుతోంది...",
    error: "లోపం",
  },
  hi: {
    idle: "बोलने के लिए दबाएं",
    listening: "सुन रहा हूँ...",
    processing: "प्रोसेस कर रहा हूँ...",
    transcribing: "लिख रहा हूँ...",
    sending: "भेज रहा हूँ...",
    responding: "सोच रहा हूँ...",
    speaking: "बोल रहा हूँ...",
    error: "त्रुटि",
  },
};

const ERROR_MESSAGES: Record<string, Record<string, string>> = {
  en: {
    mic_denied: "Microphone access is required for voice input. Please allow microphone access in your browser settings.",
    mic_unavailable: "Voice input is unavailable on this device. You can continue using text.",
    stt_unsupported: "Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.",
    stt_failed: "Speech recognition failed. Please try again.",
    stt_empty: "No speech was detected. Please try again.",
    stt_timeout: "Listening timed out. Please try again.",
    network: "Network error. Please check your connection and try again.",
    tts_unavailable: "Text-to-speech is unavailable on this device.",
    lang_mismatch: "Your selected language is {selected}, but the detected speech appears to be {detected}. Switch language?",
  },
  te: {
    mic_denied: "వాయిస్ ఇన్‌పుట్ కోసం మైక్రోఫోన్ యాక్సెస్ అవసరం. దయచేసి బ్రౌజర్ సెట్టింగ్‌లలో మైక్రోఫోన్ ను అనుమతించండి.",
    mic_unavailable: "ఈ పరికరంలో వాయిస్ ఇన్‌పుట్ అందుబాటులో లేదు. టెక్స్ట్ ఉపయోగించి కొనసాగించవచ్చు.",
    stt_unsupported: "ఈ బ్రౌజర్‌లో స్పీచ్ రికగ్నిషన్ అందుబాటులో లేదు. దయచేసి Chrome, Edge లేదా Safari వాడండి.",
    stt_failed: "స్పీచ్ రికగ్నిషన్ విఫలమైంది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    stt_empty: "మాట గుర్తించబడలేదు. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    stt_timeout: "వినడం సమయం ముగిసింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    network: "నెట్‌వర్క్ లోపం. దయచేసి మీ కనెక్షన్ తనిఖీ చేయండి.",
    tts_unavailable: "ఈ పరికరంలో టెక్స్ట్-టు-స్పీచ్ అందుబాటులో లేదు.",
    lang_mismatch: "మీరు {selected} ఎంచుకున్నారు, కానీ గుర్తించిన భాష {detected}. భాష మార్చాలా?",
  },
  hi: {
    mic_denied: "वॉइस इनपुट के लिए माइक्रोफ़ोन एक्सेस आवश्यक है। कृपया ब्राउज़र सेटिंग्स में माइक्रोफ़ोन की अनुमति दें।",
    mic_unavailable: "इस डिवाइस पर वॉइस इनपुट उपलब्ध नहीं है। आप टेक्स्ट का उपयोग कर सकते हैं।",
    stt_unsupported: "इस ब्राउज़र में स्पीच रिकग्निशन उपलब्ध नहीं है। कृपया Chrome, Edge या Safari उपयोग करें।",
    stt_failed: "स्पीच रिकग्निशन विफल हुई। कृपया पुनः प्रयास करें।",
    stt_empty: "कोई आवाज़ नहीं मिली। कृपया पुनः प्रयास करें।",
    stt_timeout: "सुनने का समय समाप्त हो गया। कृपया पुनः प्रयास करें।",
    network: "नेटवर्क त्रुटि। कृपया अपना कनेक्शन जांचें।",
    tts_unavailable: "इस डिवाइस पर टेक्स्ट-टू-स्पीच उपलब्ध नहीं है।",
    lang_mismatch: "आपकी चयनित भाषा {selected} है, लेकिन पहचानी गई भाषा {detected} है। भाषा बदलें?",
  },
};

/* ===================================================================
 * Helpers
 * =================================================================*/

/** Check if Web Speech API is available */
function getSpeechRecognitionClass(): (new () => SpeechRecognition) | null {
  if (typeof window === "undefined") return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

function isTTSAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/** Strip markdown bold/italic for TTS readability */
function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/#{1,6}\s/g, "")
    .replace(/---+/g, "")
    .replace(/[✅❌✓✗🔍📄📝🎁📚⚠🎯🆕📢⏰🏛️🤖👋•🔔🔊⏹🎤🔴]/g, "")
    .replace(/\[.*?\]\(.*?\)/g, "")
    .trim();
}

/* ===================================================================
 * Component
 * =================================================================*/
export default function ChatbotPage() {
  const router = useRouter();

  // Chat state
  const { language, setLanguage } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  // Voice state
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [sttSupported, setSttSupported] = useState(false);
  const [ttsSupported, setTtsSupported] = useState(false);
  const [voiceConversation, setVoiceConversation] = useState(false);
  const [speakingMsgIndex, setSpeakingMsgIndex] = useState<number | null>(null);
  const [showLangMismatch, setShowLangMismatch] = useState<{
    detected: string;
    text: string;
  } | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* ---- Init ---- */
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }
    api.getUnreadCount().then((d) => setUnreadCount(d.unread_count)).catch(() => {});
    setSttSupported(!!getSpeechRecognitionClass());
    setTtsSupported(isTTSAvailable());
  }, [router]);

  /* ---- Welcome message on language change ---- */
  useEffect(() => {
    setMessages([
      { role: "assistant", message: WELCOME_MESSAGES[language] || WELCOME_MESSAGES.en },
    ]);
    setSessionId(null);
  }, [language]);

  /* ---- Auto-scroll ---- */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, voiceState]);

  /* ---- Cleanup recognition on unmount ---- */
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      window.speechSynthesis?.cancel();
    };
  }, []);

  /* ---- Language helpers ---- */
  const langConfig = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];
  const t = STATUS_LABELS[language] || STATUS_LABELS.en;
  const err = ERROR_MESSAGES[language] || ERROR_MESSAGES.en;

  /* ==============================================================
   * TEXT-TO-SPEECH
   * ============================================================*/
  const speakText = useCallback(
    (text: string, msgIndex: number) => {
      if (!isTTSAvailable()) {
        setVoiceError(err.tts_unavailable);
        return;
      }

      // Stop any current speech
      window.speechSynthesis.cancel();

      const cleaned = stripMarkdown(text);
      if (!cleaned) return;

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.lang = langConfig.ttsLang;
      utterance.rate = 0.95;
      utterance.pitch = 1;

      // Try to find a matching voice
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find((v) => v.lang === langConfig.ttsLang);
      const fallback = voices.find((v) => v.lang.startsWith(langConfig.ttsLang.split("-")[0]));
      if (preferred) utterance.voice = preferred;
      else if (fallback) utterance.voice = fallback;

      utterance.onstart = () => {
        setSpeakingMsgIndex(msgIndex);
        setVoiceState("speaking");
      };
      utterance.onend = () => {
        setSpeakingMsgIndex(null);
        setVoiceState("idle");
        // Voice conversation: auto-start listening after response finishes
        if (voiceConversation) {
          setTimeout(() => startListening(), 500);
        }
      };
      utterance.onerror = () => {
        setSpeakingMsgIndex(null);
        setVoiceState("idle");
      };

      synthRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    [langConfig, err, voiceConversation],
  );

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis?.cancel();
    setSpeakingMsgIndex(null);
    setVoiceState("idle");
  }, []);

  /* ==============================================================
   * SEND MESSAGE (shared by text and voice input)
   * ============================================================*/
  const sendMessage = useCallback(
    async (text: string, source: "text" | "voice" = "text") => {
      const userMessage = text.trim();
      if (!userMessage || loading) return;

      setInput("");
      setVoiceError(null);
      setShowLangMismatch(null);

      setMessages((prev) => [
        ...prev,
        { role: "user", message: userMessage, source },
      ]);
      setLoading(true);
      setVoiceState("sending");

      try {
        const data = (await api.askChatbot(
          userMessage,
          sessionId || undefined,
          language,
        )) as {
          answer: string;
          citations: { scheme_name: string; slug: string; relevance: number }[];
          confidence: number;
          session_id: string;
          language?: string;
        };

        if (data.language && data.language !== language && (data.language === "en" || data.language === "te" || data.language === "hi")) {
          setLanguage(data.language as SupportedLanguage);
        }

        setSessionId(data.session_id);
        setVoiceState("responding");

        const assistantMsg: ChatMessage = {
          role: "assistant",
          message: data.answer,
          citations: data.citations,
          confidence: data.confidence,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Voice conversation: auto-speak the response
        if (voiceConversation && source === "voice") {
          // Small delay to let React render
          setTimeout(() => {
            const idx = messages.length + 1; // +1 user, +1 assistant (0-indexed)
            speakText(data.answer, idx);
          }, 300);
        } else {
          setVoiceState("idle");
        }
      } catch {
        const errorMsg =
          language === "te"
            ? "క్షమించండి, ఒక లోపం సంభవించింది. దయచేసి మళ్ళీ ప్రయత్నించండి."
            : language === "hi"
              ? "क्षमा करें, एक त्रुटि हुई। कृपया पुनः प्रयास करें।"
              : "Sorry, I encountered an error. Please try again.";
        setMessages((prev) => [...prev, { role: "assistant", message: errorMsg }]);
        setVoiceState("error");
        setTimeout(() => setVoiceState("idle"), 2000);
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId, language, voiceConversation, messages.length, speakText],
  );

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) sendMessage(input, "text");
  };

  /* ==============================================================
   * SPEECH RECOGNITION (STT)
   * ============================================================*/
  const startListening = useCallback(() => {
    const SpeechRecognitionClass = getSpeechRecognitionClass();
    if (!SpeechRecognitionClass) {
      setVoiceError(err.stt_unsupported);
      setVoiceState("error");
      setTimeout(() => setVoiceState("idle"), 3000);
      return;
    }

    setVoiceError(null);
    setShowLangMismatch(null);

    const recognition = new SpeechRecognitionClass();
    recognition.lang = langConfig.sttLang;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    let finalTranscript = "";
    let hasResult = false;

    recognition.onstart = () => {
      setVoiceState("listening");
      setInput("");
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      hasResult = true;
      let interim = "";
      finalTranscript = "";

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      // Show interim text in input
      setInput(finalTranscript || interim);
    };

    recognition.onend = () => {
      recognitionRef.current = null;

      if (!hasResult || !finalTranscript.trim()) {
        setVoiceState("idle");
        if (hasResult && !finalTranscript.trim()) {
          setVoiceError(err.stt_empty);
        }
        return;
      }

      setVoiceState("processing");
      const transcribed = finalTranscript.trim();
      setInput(transcribed);

      // In voice conversation mode: auto-send
      if (voiceConversation) {
        sendMessage(transcribed, "voice");
      }
      // Normal mode: leave the text in the input for user to review/edit/send
      else {
        setVoiceState("idle");
        inputRef.current?.focus();
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      recognitionRef.current = null;

      switch (event.error) {
        case "not-allowed":
          setVoiceError(err.mic_denied);
          break;
        case "no-speech":
          setVoiceError(err.stt_empty);
          break;
        case "audio-capture":
          setVoiceError(err.mic_unavailable);
          break;
        case "network":
          setVoiceError(err.network);
          break;
        case "aborted":
          // User-initiated abort, no error
          break;
        default:
          setVoiceError(err.stt_failed);
      }

      setVoiceState("error");
      setTimeout(() => setVoiceState("idle"), 3000);
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
    } catch {
      setVoiceError(err.stt_failed);
      setVoiceState("error");
      setTimeout(() => setVoiceState("idle"), 3000);
    }
  }, [langConfig, err, voiceConversation, sendMessage]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  const toggleListening = useCallback(() => {
    if (voiceState === "listening") {
      stopListening();
    } else if (voiceState === "idle" || voiceState === "error") {
      startListening();
    }
  }, [voiceState, startListening, stopListening]);

  /* ---- Language change ---- */
  const handleLanguageChange = (newLang: string) => {
    // Stop any ongoing speech/recognition
    recognitionRef.current?.abort();
    window.speechSynthesis?.cancel();
    setSpeakingMsgIndex(null);
    setVoiceState("idle");
    setVoiceError(null);
    setShowLangMismatch(null);

    setLanguage(newLang as SupportedLanguage);
  };

  /* ---- Derived values ---- */
  const currentQuickQuestions = QUICK_QUESTIONS[language] || QUICK_QUESTIONS.en;
  const isListening = voiceState === "listening";
  const isProcessing = ["processing", "transcribing", "sending", "responding"].includes(voiceState);
  const isSpeaking = voiceState === "speaking";

  /* ==============================================================
   * RENDER
   * ============================================================*/
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Navigation */}
      <Navbar unreadCount={unreadCount} />

      <div className="chat-container">
        {/* ===== Header ===== */}
        <div className="chat-header">
          <div>
            <h2 style={{ fontSize: "1.25rem", marginBottom: "0.125rem" }}>🤖 AI Scheme Assistant</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              {language === "te"
                ? "అధికారిక ప్రభుత్వ పథకాల ఆధారంగా"
                : language === "hi"
                  ? "आधिकारिक सरकारी योजनाओं पर आधारित"
                  : "Powered by official government scheme documents"}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.150rem", flexWrap: "wrap" }}>
            {/* Voice conversation toggle */}
            {sttSupported && (
              <label className="voice-conv-toggle" title="Auto voice conversation mode">
                <input
                  type="checkbox"
                  checked={voiceConversation}
                  onChange={(e) => setVoiceConversation(e.target.checked)}
                  style={{ accentColor: "var(--primary-light)" }}
                />
                <span>{language === "te" ? "వాయిస్ సంభాషణ" : language === "hi" ? "वॉइस वार्तालाप" : "Voice Conversation"}</span>
              </label>
            )}
            {/* Language selector */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.3150rem" }}>
              <span style={{ fontSize: "0.150rem", color: "var(--text-muted)" }}>
                {language === "te" ? "భాష:" : language === "hi" ? "भाषा:" : "Language:"}
              </span>
              <select
                className="select"
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                style={{ minWidth: "120px", fontSize: "0.8125rem" }}
                id="chatbot-language-selector"
                aria-label="Select chatbot language"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.flag} {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* ===== Messages ===== */}
        <div className="chat-messages" role="log" aria-live="polite" aria-label="Chat messages">
          {messages.map((msg, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column" }}>
              <div className={`chat-bubble ${msg.role}`}>
                {/* Voice source badge */}
                {msg.role === "user" && msg.source === "voice" && (
                  <div className="msg-source">🎤 Voice</div>
                )}
                <div style={{ whiteSpace: "pre-wrap" }}>{msg.message}</div>
              </div>

              {/* Assistant TTS button */}
              {msg.role === "assistant" && i > 0 && ttsSupported && (
                <div style={{ alignSelf: "flex-start", marginTop: "0.25rem" }}>
                  {speakingMsgIndex === i ? (
                    <button
                      className="tts-btn speaking"
                      onClick={stopSpeaking}
                      aria-label="Stop reading response aloud"
                    >
                      ⏹ {language === "te" ? "ఆపు" : language === "hi" ? "रोकें" : "Stop"}
                    </button>
                  ) : (
                    <button
                      className="tts-btn"
                      onClick={() => speakText(msg.message, i)}
                      aria-label="Read response aloud"
                      disabled={isSpeaking && speakingMsgIndex !== i}
                    >
                      🔊 {language === "te" ? "వినండి" : language === "hi" ? "सुनें" : "Listen"}
                    </button>
                  )}
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{
                  alignSelf: "flex-start", marginTop: "0.3150rem",
                  padding: "0.625rem 0.8150rem", background: "var(--bg-sidebar)",
                  borderRadius: "var(--radius-sm)", maxWidth: "80%", fontSize: "0.8125rem",
                }}>
                  <div style={{ fontWeight: 600, marginBottom: "0.25rem", color: "var(--text-secondary)" }}>
                    📚 {language === "te" ? "మూలాలు:" : language === "hi" ? "स्रोत:" : "Sources:"}
                  </div>
                  {msg.citations.map((c, ci) => (
                    <Link
                      key={ci}
                      href={`/schemes/${c.slug}`}
                      style={{
                        display: "block", color: "var(--primary-light)", textDecoration: "none",
                        padding: "0.125rem 0", fontSize: "0.8125rem",
                      }}
                    >
                      {c.scheme_name} ({Math.round(c.relevance * 100)}%)
                    </Link>
                  ))}
                  {msg.confidence !== undefined && (
                    <div style={{ marginTop: "0.25rem", color: "var(--text-muted)", fontSize: "0.150rem" }}>
                      {language === "te" ? "నమ్మకం" : language === "hi" ? "विश्वास" : "Confidence"}:{" "}
                      {Math.round(msg.confidence * 100)}%
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Loading / Voice status */}
          {loading && (
            <div className="chat-bubble assistant" style={{ opacity: 0.7 }}>
              <span style={{ animation: "pulse-glow 1.5s infinite" }}>{t.responding}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ===== Voice Status Bar ===== */}
        {voiceState !== "idle" && voiceState !== "error" && voiceState !== "speaking" && !loading && (
          <div
            className={`voice-status ${isListening ? "listening" : "processing"}`}
            role="status"
            aria-live="assertive"
          >
            {isListening && <span className="recording-dot" />}
            {isListening && <span>🔴</span>}
            {isProcessing && <span>⏳</span>}
            <span>{t[voiceState]}</span>
            {isListening && (
              <button
                onClick={stopListening}
                className="btn btn-ghost btn-sm"
                style={{ marginLeft: "auto", fontSize: "0.150rem" }}
              >
                {language === "te" ? "ఆపు" : language === "hi" ? "रोकें" : "Stop"}
              </button>
            )}
          </div>
        )}

        {/* Speaking status */}
        {isSpeaking && (
          <div className="voice-status processing" role="status" aria-live="polite">
            <span>🔊</span>
            <span>{t.speaking}</span>
            <button
              onClick={stopSpeaking}
              className="btn btn-ghost btn-sm"
              style={{ marginLeft: "auto", fontSize: "0.150rem" }}
            >
              ⏹ {language === "te" ? "ఆపు" : language === "hi" ? "रोकें" : "Stop"}
            </button>
          </div>
        )}

        {/* ===== Error Banner ===== */}
        {voiceError && (
          <div
            className="voice-status error"
            role="alert"
            style={{ cursor: "pointer" }}
            onClick={() => setVoiceError(null)}
          >
            <span>⚠️</span>
            <span>{voiceError}</span>
            <span style={{ marginLeft: "auto", opacity: 0.5, fontSize: "0.150rem" }}>✕</span>
          </div>
        )}

        {/* ===== Language mismatch dialog ===== */}
        {showLangMismatch && (
          <div className="voice-status processing" role="alert">
            <span>🌐</span>
            <span>
              {err.lang_mismatch
                .replace("{selected}", langConfig.name)
                .replace("{detected}", showLangMismatch.detected)}
            </span>
            <div style={{ marginLeft: "auto", display: "flex", gap: "0.3150rem" }}>
              <button
                className="btn btn-primary btn-sm"
                style={{ fontSize: "0.68150rem" }}
                onClick={() => {
                  setShowLangMismatch(null);
                  sendMessage(showLangMismatch.text, "voice");
                }}
              >
                {language === "te" ? "పంపు" : language === "hi" ? "भेजें" : "Send anyway"}
              </button>
              <button
                className="btn btn-ghost btn-sm"
                style={{ fontSize: "0.68150rem" }}
                onClick={() => setShowLangMismatch(null)}
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* ===== Quick Questions (only on first screen) ===== */}
        {messages.length <= 1 && (
          <div style={{ padding: "0.5rem 0", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {currentQuickQuestions.map((q, i) => (
              <button
                key={i}
                className="btn btn-outline btn-sm"
                onClick={() => setInput(q)}
                style={{ fontSize: "0.8125rem" }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* ===== Input Area ===== */}
        <form onSubmit={handleFormSubmit} className="chat-input-area">
          {/* Microphone Button */}
          <button
            type="button"
            className={`voice-btn ${isListening ? "listening" : ""} ${isProcessing ? "processing" : ""}`}
            onClick={toggleListening}
            disabled={loading || isProcessing || isSpeaking || !sttSupported}
            aria-label={
              !sttSupported
                ? (language === "te" ? "వాయిస్ ఇన్‌పుట్ అందుబాటులో లేదు" : language === "hi" ? "वॉइस इनपुट उपलब्ध नहीं" : "Voice input unavailable")
                : isListening
                  ? (language === "te" ? "రికార్డింగ్ ఆపు" : language === "hi" ? "रिकॉर्डिंग बंद करें" : "Stop recording")
                  : (language === "te" ? "వాయిస్ ఇన్‌పుట్ ప్రారంభించు" : language === "hi" ? "वॉइस इनपुट शुरू करें" : "Start voice input")
            }
            title={!sttSupported ? err.stt_unsupported : t[voiceState]}
          >
            {isListening ? "🔴" : isProcessing ? "⏳" : "🎤"}
          </button>

          {/* Text Input */}
          <input
            ref={inputRef}
            className="input"
            placeholder={
              language === "te"
                ? "ప్రభుత్వ పథకాల గురించి అడగండి..."
                : language === "hi"
                  ? "सरकारी योजनाओं के बारे में पूछें..."
                  : "Ask about government schemes..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || isListening}
            autoFocus
            aria-label={
              language === "te"
                ? "మీ ప్రశ్న టైప్ చేయండి"
                : language === "hi"
                  ? "अपना प्रश्न टाइप करें"
                  : "Type your question"
            }
            style={{ flex: 1 }}
          />

          {/* Send Button */}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !input.trim() || isListening}
            aria-label={language === "te" ? "పంపు" : language === "hi" ? "भेजें" : "Send message"}
            style={{ minWidth: "60px" }}
          >
            {loading ? "⏳" : "➤"}
          </button>
        </form>

        {/* ===== Footer ===== */}
        <div
          style={{
            padding: "0.3150rem 0 0.5rem",
            textAlign: "center",
            fontSize: "0.68150rem",
            color: "var(--text-muted)",
          }}
        >
          {sttSupported ? (
            <>
              🎤{" "}
              {language === "te"
                ? "మైక్రోఫోన్ బటన్ నొక్కి వాయిస్‌తో అడగండి"
                : language === "hi"
                  ? "माइक्रोफ़ोन बटन दबाकर आवाज़ से पूछें"
                  : "Press the microphone button to ask with your voice"}
              {voiceConversation && (
                <span>
                  {" · "}
                  {language === "te"
                    ? "వాయిస్ సంభాషణ చేతనం"
                    : language === "hi"
                      ? "वॉइस वार्तालाप सक्रिय"
                      : "Voice conversation active"}
                </span>
              )}
            </>
          ) : (
            <>
              ⌨️{" "}
              {language === "te"
                ? "ఈ బ్రౌజర్‌లో వాయిస్ ఇన్‌పుట్ అందుబాటులో లేదు. టెక్స్ట్ ఉపయోగించండి."
                : language === "hi"
                  ? "इस ब्राउज़र में वॉइस इनपुट उपलब्ध नहीं। टेक्स्ट उपयोग करें।"
                  : "Voice input unavailable in this browser. Use text input."}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
