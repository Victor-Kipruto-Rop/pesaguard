'use client';

import { useLocale } from '../lib/i18n';

export default function LocaleSwitcher() {
  const { locale, setLocale } = useLocale();

  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span className="muted" style={{ fontSize: 12 }}>🌐</span>
      <select
        value={locale}
        onChange={(event) => setLocale(event.target.value as 'en' | 'sw')}
        style={{ borderRadius: 999, border: '1px solid var(--border)', background: 'var(--panel)', color: 'var(--text)', padding: '4px 8px' }}
      >
        <option value="en">EN</option>
        <option value="sw">SW</option>
      </select>
    </label>
  );
}
