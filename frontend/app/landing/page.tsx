'use client';

import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

export default function LandingPage() {
  const { t, format } = useLocale();
  const steps = t<{ title: string; body: string }[]>('landing.steps');
  const trust = t<string[]>('landing.trust');

  return (
    <main className="publicMain">
      <PageHeader
        eyebrow={t('landing.eyebrow')}
        title={t('landing.title')}
        summary={t('landing.summary')}
        actions={
          <>
            <a className="primaryBtn" href="/contact">{t('landing.ctaPrimary')}</a>
            <a className="secondaryBtn" href="/security">{t('landing.ctaSecondary')}</a>
          </>
        }
      />

      <section className="grid twoUp">
        <article className="card">
          <div className="sectionTitle">{t('landing.problemTitle')}</div>
          <p className="muted">{t('landing.problemBody')}</p>
        </article>
        <article className="card">
          <div className="sectionTitle">{t('landing.solutionTitle')}</div>
          <p className="muted">{t('landing.solutionBody')}</p>
        </article>
      </section>

      <section className="card">
        <div className="sectionTitle">{t('landing.howItWorks')}</div>
        <div className="readinessGrid">
          {steps.map((step, index) => (
            <article key={step.title} className="assetCard">
              <div className="eyebrow">{format('landing.stepLabel', { value: index + 1 })}</div>
              <h3>{step.title}</h3>
              <p className="muted">{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="sectionTitle">{t('landing.trustTitle')}</div>
        <ul className="stackList">
          {trust.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
