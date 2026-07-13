import { useEffect, useState } from 'react';
import en from '../locales/en.json';
import sw from '../locales/sw.json';

export type LocaleCode = 'en' | 'sw';

declare global {
  interface Window {
    __PESAGUARD_LOCALE__?: string;
    __PESAGUARD_PREFERENCES__?: { locale?: string };
  }
}

const translations = { en, sw } as const;
const STORAGE_KEY = 'pesaguard.locale';
const EVENT_NAME = 'pesaguard.locale-change';

export function normalizeLocaleCandidate(value: string | null | undefined): LocaleCode | null {
  if (!value) {
    return null;
  }

  const normalized = value.trim().toLowerCase();
  if (normalized.startsWith('sw')) {
    return 'sw';
  }
  if (normalized.startsWith('en')) {
    return 'en';
  }
  return null;
}

export function getInitialLocale(): LocaleCode {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === 'sw' || saved === 'en') {
    return saved;
  }

  const contextLocale = normalizeLocaleCandidate(
    window.__PESAGUARD_LOCALE__ || window.__PESAGUARD_PREFERENCES__?.locale,
  );
  if (contextLocale) {
    return contextLocale;
  }

  const browserLocale = typeof navigator !== 'undefined' && navigator.language.toLowerCase().startsWith('sw') ? 'sw' : 'en';
  return browserLocale;
}

export function setLocale(locale: LocaleCode) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, locale);
  window.__PESAGUARD_LOCALE__ = locale;
  window.__PESAGUARD_PREFERENCES__ = { ...(window.__PESAGUARD_PREFERENCES__ || {}), locale };
  document.documentElement.lang = locale;
  void (async () => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      const adminToken = window.localStorage.getItem('pesaguard.admin_token');
      if (adminToken) {
        headers['X-Admin-Token'] = adminToken;
      }
      await fetch('/tenant/current/locale', {
        method: 'POST',
        headers,
        body: JSON.stringify({ preferred_locale: locale }),
      });
    } catch (error) {
      console.error(error);
    }
  })();
  window.dispatchEvent(new Event(EVENT_NAME));
}

function getValueByKey(source: Record<string, unknown>, key: string, useCamelCaseFallback = false): unknown {
  const parts = key.split('.');
  let current: unknown = source;

  for (let index = 0; index < parts.length; index += 1) {
    const part = parts[index];

    if (current && typeof current === 'object' && part in (current as Record<string, unknown>)) {
      current = (current as Record<string, unknown>)[part];
      continue;
    }

    if (useCamelCaseFallback && index < parts.length - 1) {
      const combined = part + parts.slice(index + 1).reduce((accumulator, segment) => {
        return accumulator + segment.charAt(0).toUpperCase() + segment.slice(1);
      }, '');

      if (current && typeof current === 'object' && combined in (current as Record<string, unknown>)) {
        return (current as Record<string, unknown>)[combined];
      }
    }

    return undefined;
  }

  return current;
}

export function getText<T = string>(key: string, locale: LocaleCode = getInitialLocale()): T {
  const current = translations[locale];
  const fallback = translations.en;

  const value = getValueByKey(current, key);
  if (typeof value === 'string' || Array.isArray(value)) {
    return value as T;
  }

  const fallbackValue = getValueByKey(fallback, key, true);
  if (typeof fallbackValue === 'string' || Array.isArray(fallbackValue)) {
    return fallbackValue as T;
  }

  return key as T;
}

export function useLocale() {
  const [locale, setLocaleState] = useState<LocaleCode>(getInitialLocale());

  useEffect(() => {
    const listener = () => {
      setLocaleState(getInitialLocale());
    };

    window.addEventListener(EVENT_NAME, listener);

    // Fetch tenant preferences from the backend once on mount and apply preferred locale
    // if the client has not already chosen a locale.
    (async () => {
      try {
        const saved = window.localStorage.getItem(STORAGE_KEY);
        if (!saved) {
          const resp = await fetch('/tenant/current');
          if (resp && resp.ok) {
            const json = await resp.json();
            const candidate = normalizeLocaleCandidate(json?.preferred_locale);
            if (candidate) {
              setLocale(candidate);
            }
          }
        }
      } catch (e) {
        // network failures should not block the app; silently ignore
      }
    })();

    return () => window.removeEventListener(EVENT_NAME, listener);
  }, []);

  return {
    locale,
    setLocale: (next: LocaleCode) => setLocale(next),
    t: <T = string>(key: string) => getText<T>(key, locale),
  };
}
