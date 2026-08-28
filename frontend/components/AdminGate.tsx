'use client';

import { useEffect, useState } from 'react';
import { useLocale } from '../lib/i18n';

export default function AdminGate({ children }: { children: React.ReactNode }) {
  const { t } = useLocale();
  const [hasAccess, setHasAccess] = useState<boolean | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    setHasAccess(!!window.localStorage.getItem('pesaguard.admin_token'));
  }, []);

  if (hasAccess === null) {
    return (
      <main className="shell" style={{ minHeight: '70vh', display: 'grid', placeItems: 'center' }}>
        <p className="muted">{t('common.loading')}</p>
      </main>
    );
  }

  if (!hasAccess) {
    return (
      <main className="shell">
        <section className="card">
          <p className="eyebrow">Premium admin access</p>
          <h1>Unlock the premium admin console</h1>
          <p className="muted">
            Administrator pages are reserved for premium customers with a valid admin API token. Enter your token or upgrade to access advanced tenant controls, operational monitoring, and audit workflows.
          </p>
          <div className="sectionActions" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 20 }}>
            <a className="primaryBtn" href="/pricing">
              View premium plans
            </a>
            <button
              className="secondaryBtn"
              type="button"
              onClick={() => {
                const token = window.prompt('Enter admin token');
                if (token) {
                  window.localStorage.setItem('pesaguard.admin_token', token);
                  window.location.reload();
                }
              }}
            >
              Enter admin token
            </button>
          </div>
        </section>
      </main>
    );
  }

  return <>{children}</>;
}
