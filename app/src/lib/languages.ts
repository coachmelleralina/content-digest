// Supported card languages (feature 017, issue #16). Pure module: the
// per-card UA|RU|EN switcher renders from SUPPORTED_LANGUAGES/languageLabel,
// and the api client types its translate payload with Language. Mirrors the
// backend contract (issue #14): POST /api/cards/{id}/translate {language}.

export const SUPPORTED_LANGUAGES = ['uk', 'ru', 'en'] as const;

export type Language = (typeof SUPPORTED_LANGUAGES)[number];

const LABELS: Record<Language, string> = { uk: 'UA', ru: 'RU', en: 'EN' };

/** Compact switcher label for a supported language code (uk → 'UA'). */
export const languageLabel = (code: Language): string => LABELS[code];

/** Type guard: is this string one of the supported language codes? */
export const isSupportedLanguage = (s: string): s is Language =>
  (SUPPORTED_LANGUAGES as readonly string[]).includes(s);
