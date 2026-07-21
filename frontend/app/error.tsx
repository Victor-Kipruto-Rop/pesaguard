'use client';

import PulseLine from '../components/PulseLine';
import { useLocale } from '../lib/i18n';

export default function ErrorPage({ reset }: { reset: () => void }) {
  const { t } = useLocale();

  return (
    <main className="shell">
      <section className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <PulseLine height={36} />
        <h1>{t('errors.serverTitle')}</h1>
        <p className="muted">{t('errors.serverBody')}</p>
        <div className="heroActions" style={{ justifyContent: 'center' }}>
          <button className="primaryBtn" onClick={reset}>{t('errors.retry')}</button>
          <a className="secondaryBtn" href="/status">{t('errors.viewStatus')}</a>
        </div>
      </section>
    </main>
  );
}
