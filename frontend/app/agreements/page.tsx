'use client';

import { useLocale } from '../../lib/i18n';
import ScopeNotice from '../../components/ScopeNotice';
import OnboardingLinks from '../../components/OnboardingLinks';

interface AgreementItem {
  title: string;
  summary: string;
  href: string;
}

interface AgreementHighlight {
  title: string;
  body: string;
}

export default function AgreementsPage() {
  const { t } = useLocale();
  const agreements = t<AgreementItem[]>('agreementsPage.items');
  const highlights = t<AgreementHighlight[]>('agreementsPage.highlights');

  return (
    <main className="pageShell">
      <ScopeNotice />

      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">{t('agreementsPage.badge')}</div>
          <p className="eyebrow">{t('agreementsPage.eyebrow')}</p>
          <h1>{t('agreementsPage.title')}</h1>
          <p className="muted">{t('agreementsPage.summary')}</p>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">{t('common.value')}</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>{t('agreementsPage.packTitle')}</h2>
        <p className="muted">{t('agreementsPage.packSummary')}</p>
        <div className="grid">
          {agreements.map((item) => (
            <article key={item.title} className="assetCard">
              <div className="eyebrow">{t('common.draft')}</div>
              <h3>{item.title}</h3>
              <p className="muted">{item.summary}</p>
              <div className="downloadRow">
                <a className="primaryBtn" href={item.href} download>{t('common.download')}</a>
                <a className="secondaryBtn" href={item.href}>{t('common.preview')}</a>
              </div>
            </article>
          ))}
        </div>
      </section>

      <OnboardingLinks />
    </main>
  );
}
