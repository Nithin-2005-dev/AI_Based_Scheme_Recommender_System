import { en } from "./en";
import { te } from "./te";
import { hi } from "./hi";

export type SupportedLanguage = "en" | "te" | "hi";

export interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "en", name: "English", nativeName: "English", flag: "🇬🇧" },
  { code: "te", name: "Telugu", nativeName: "తెలుగు", flag: "🇮🇳" },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी", flag: "🇮🇳" },
];

export const translations: Record<SupportedLanguage, typeof en> = {
  en,
  te,
  hi,
};

export { en, te, hi };
