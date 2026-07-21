'use client';

import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

export default function SandboxPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <div className="sandboxBanner">{t('sandbox.banner')}</div>
      <PageHeader eyebrow={t('sandbox.eyebrow')} title={t('sandbox.title')} summary={t('sandbox.summary')} showPulse={false} />
      <section className="card">
        <div className="sectionTitle">{t('sandbox.whatTitle')}</div>
        <ul className="stackList">
          {t<string[]>('sandbox.items').map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <a className="primaryBtn" href="/transactions">{t('sandbox.tryTransactions')}</a>
      </section>
    </main>
  );
}
