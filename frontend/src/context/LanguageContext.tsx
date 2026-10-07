"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { translations, SUPPORTED_LANGUAGES, SupportedLanguage, LanguageOption } from "@/locales";

interface LanguageContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string, fallback?: string, vars?: Record<string, string | number>) => string;
  supportedLanguages: LanguageOption[];
}

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
  t: (key: string, fallback?: string) => fallback || key,
  supportedLanguages: SUPPORTED_LANGUAGES,
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<SupportedLanguage>("en");
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("preferred_language") as SupportedLanguage | null;
      if (saved && (saved === "en" || saved === "te" || saved === "hi")) {
        setLanguageState(saved);
        document.documentElement.lang = saved;
      }
    } catch {
      // localStorage may fail in some environments
    } finally {
      setIsHydrated(true);
    }
  }, []);

  const setLanguage = useCallback((newLang: SupportedLanguage) => {
    setLanguageState(newLang);
    try {
      localStorage.setItem("preferred_language", newLang);
      document.documentElement.lang = newLang;
      window.dispatchEvent(new CustomEvent("languageChanged", { detail: newLang }));
    } catch {
      // ignore
    }
  }, []);

  const t = useCallback(
    (keyPath: string, fallback?: string, vars?: Record<string, string | number>): string => {
      const keys = keyPath.split(".");
      const currentDict = translations[language] || translations.en;
      const defaultDict = translations.en;

      let value: unknown = currentDict;
      for (const k of keys) {
        if (value && typeof value === "object" && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          value = undefined;
          break;
        }
      }

      // Fallback to English if missing in selected language
      if (value === undefined || typeof value !== "string") {
        let fallbackVal: unknown = defaultDict;
        for (const k of keys) {
          if (fallbackVal && typeof fallbackVal === "object" && k in fallbackVal) {
            fallbackVal = (fallbackVal as Record<string, unknown>)[k];
          } else {
            fallbackVal = undefined;
            break;
          }
        }
        if (typeof fallbackVal === "string") {
          value = fallbackVal;
        }
      }

      let result = typeof value === "string" ? value : (fallback || keyPath);

      if (vars && typeof result === "string") {
        for (const [varKey, varVal] of Object.entries(vars)) {
          result = result.replace(new RegExp(`\\{${varKey}\\}`, "g"), String(varVal));
        }
      }

      return result;
    },
    [language]
  );

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, supportedLanguages: SUPPORTED_LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
