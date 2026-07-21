import { useEffect, useState } from 'react';
import en from '../locales/en.json';
import sw from '../locales/sw.json';
import { getUserId } from './userId';

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

function applyLocaleLocally(locale: LocaleCode) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, locale);
  window.__PESAGUARD_LOCALE__ = locale;
  window.__PESAGUARD_PREFERENCES__ = { ...(window.__PESAGUARD_PREFERENCES__ || {}), locale };
  document.documentElement.lang = locale;
}

export function setLocale(locale: LocaleCode) {
  if (typeof window === 'undefined') {
    return;
  }

  applyLocaleLocally(locale);

  void (async () => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      const adminToken = window.localStorage.getItem('pesaguard.admin_token');
      if (adminToken) {
        headers['X-Admin-Token'] = adminToken;
      }
      await fetch('/tenant/current/user-locale', {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: getUserId(), preferred_locale: locale }),
      });
    } catch (error) {
      console.error(error);
    }
  })();

  window.dispatchEvent(new Event(EVENT_NAME));
}

export function clearUserLocale() {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);

  void (async () => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      const adminToken = window.localStorage.getItem('pesaguard.admin_token');
      if (adminToken) {
        headers['X-Admin-Token'] = adminToken;
      }
      const resp = await fetch('/tenant/current/user-locale', {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: getUserId(), preferred_locale: null }),
      });
      if (resp.ok) {
        const json = await resp.json();
        const next = normalizeLocaleCandidate(json?.effective_locale) ?? 'en';
        applyLocaleLocally(next);
        window.dispatchEvent(new Event(EVENT_NAME));
      }
    } catch (error) {
      console.error(error);
    }
  })();
}

export function formatText(template: string, vars: Record<string, string | number>): string {
  return Object.entries(vars).reduce(
    (result, [key, value]) => result.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value)),
    template,
  );
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
  if (value !== undefined) {
    return value as T;
  }

  const fallbackValue = getValueByKey(fallback, key, true);
  if (fallbackValue !== undefined) {
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

    (async () => {
      try {
        const userId = getUserId();
        const resp = await fetch(`/tenant/current/locale?user_id=${encodeURIComponent(userId)}`);
        if (resp.ok) {
          const json = await resp.json();
          const candidate = normalizeLocaleCandidate(json?.effective_locale);
          if (candidate) {
            applyLocaleLocally(candidate);
            setLocaleState(candidate);
            return;
          }
        }

        const saved = window.localStorage.getItem(STORAGE_KEY);
        if (!saved) {
          const tenantResp = await fetch('/tenant/current');
          if (tenantResp.ok) {
            const json = await tenantResp.json();
            const tenantLocale = normalizeLocaleCandidate(json?.preferred_locale);
            if (tenantLocale) {
              applyLocaleLocally(tenantLocale);
              setLocaleState(tenantLocale);
            }
          }
        }
      } catch {
        // network failures should not block the app
      }
    })();

    return () => window.removeEventListener(EVENT_NAME, listener);
  }, []);

  return {
    locale,
    setLocale: (next: LocaleCode) => setLocale(next),
    clearUserLocale,
    t: <T = string>(key: string) => getText<T>(key, locale),
    format: (key: string, vars: Record<string, string | number>) => formatText(getText<string>(key, locale), vars),
  };
}
