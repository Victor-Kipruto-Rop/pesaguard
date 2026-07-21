'use client';

import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

export default function SecurityPage() {
  const { t } = useLocale();
  const sections = t<{ title: string; body: string }[]>('security.sections');

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('security.eyebrow')} title={t('security.title')} summary={t('security.summary')} />
      <section className="readinessGrid">
        {sections.map((section) => (
          <article key={section.title} className="assetCard">
            <h3>{section.title}</h3>
            <p className="muted">{section.body}</p>
          </article>
        ))}
      </section>
      <section className="card">
        <div className="sectionTitle">{t('security.docsTitle')}</div>
        <div className="downloadRow">
          <a className="secondaryBtn" href="/assets/data-processing-agreement.txt">{t('security.dpa')}</a>
          <a className="secondaryBtn" href="/assets/privacy-policy.txt">{t('security.privacy')}</a>
          <a className="secondaryBtn" href="/legal/terms">{t('security.terms')}</a>
        </div>
      </section>
    </main>
  );
}
