// Spec for feature 017 (issue #16) — supported card languages, pure module.

import { describe, expect, it } from 'vitest';
import {
  SUPPORTED_LANGUAGES,
  languageLabel,
  isSupportedLanguage,
  type Language,
} from './languages';

describe('SUPPORTED_LANGUAGES', () => {
  it('is exactly uk, ru, en in switcher order', () => {
    expect(SUPPORTED_LANGUAGES).toEqual(['uk', 'ru', 'en']);
  });
});

describe('languageLabel', () => {
  it('maps codes to compact switcher labels', () => {
    expect(languageLabel('uk')).toBe('UA');
    expect(languageLabel('ru')).toBe('RU');
    expect(languageLabel('en')).toBe('EN');
  });

  it('covers every supported language', () => {
    for (const code of SUPPORTED_LANGUAGES) {
      expect(languageLabel(code)).toMatch(/^[A-Z]{2}$/);
    }
  });
});

describe('isSupportedLanguage', () => {
  it('accepts the three supported codes', () => {
    expect(isSupportedLanguage('uk')).toBe(true);
    expect(isSupportedLanguage('ru')).toBe(true);
    expect(isSupportedLanguage('en')).toBe(true);
  });

  it('rejects anything else', () => {
    expect(isSupportedLanguage('de')).toBe(false);
    expect(isSupportedLanguage('')).toBe(false);
    expect(isSupportedLanguage('UK')).toBe(false);
    expect(isSupportedLanguage('ukr')).toBe(false);
  });

  it('narrows to Language (compile-time check)', () => {
    const raw = 'uk' as string;
    if (isSupportedLanguage(raw)) {
      const lang: Language = raw;
      expect(lang).toBe('uk');
    }
  });
});
