'use client';

import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

export default function AboutPage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('about.eyebrow')} title={t('about.title')} summary={t('about.summary')} />
      <section className="grid twoUp">
        <article className="card">
          <div className="sectionTitle">{t('about.missionTitle')}</div>
          <p className="muted">{t('about.missionBody')}</p>
        </article>
        <article className="card">
          <div className="sectionTitle">{t('about.whyTitle')}</div>
          <p className="muted">{t('about.whyBody')}</p>
        </article>
      </section>
      <section className="card">
        <div className="sectionTitle">{t('about.founderTitle')}</div>
        <p className="muted">{t('about.founderBody')}</p>
      </section>
    </main>
  );
}
