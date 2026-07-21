'use client';

import PulseLine from '../../components/PulseLine';
import { useLocale } from '../../lib/i18n';

export default function MaintenancePage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <section className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <PulseLine height={40} />
        <h1>{t('maintenance.title')}</h1>
        <p className="muted">{t('maintenance.summary')}</p>
        <a className="secondaryBtn" href="/status">{t('maintenance.statusLink')}</a>
      </section>
    </main>
  );
}
