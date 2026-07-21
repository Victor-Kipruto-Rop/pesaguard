'use client';

import PulseLine from '../components/PulseLine';
import { useLocale } from '../lib/i18n';

export default function NotFound() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <section className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <PulseLine height={36} />
        <h1>{t('errors.notFoundTitle')}</h1>
        <p className="muted">{t('errors.notFoundBody')}</p>
        <div className="heroActions" style={{ justifyContent: 'center' }}>
          <a className="primaryBtn" href="/">{t('errors.goDashboard')}</a>
          <a className="secondaryBtn" href="/landing">{t('errors.goHome')}</a>
        </div>
      </section>
    </main>
  );
}
