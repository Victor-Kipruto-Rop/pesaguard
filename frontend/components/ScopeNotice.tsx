'use client';

import { useLocale } from '../lib/i18n';

export default function ScopeNotice() {
  const { t } = useLocale();

  return (
    <div className="panel" style={{ marginBottom: 16, borderLeft: '3px solid var(--accent)' }}>
      <strong>{t('scope.label')}</strong>
      <p className="muted" style={{ marginTop: 8, marginBottom: 0 }}>{t('scope.detail')}</p>
    </div>
  );
}
