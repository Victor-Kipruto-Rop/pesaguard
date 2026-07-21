'use client';

import { useLocale } from '../../lib/i18n';
import ScopeNotice from '../../components/ScopeNotice';

interface PolicyItem {
  title: string;
  summary: string;
  href: string;
}

interface PolicyHighlight {
  title: string;
  body: string;
}

export default function PoliciesPage() {
  const { t } = useLocale();
  const policyItems = t<PolicyItem[]>('policiesPage.items');
  const highlights = t<PolicyHighlight[]>('policiesPage.highlights');

  return (
    <main className="pageShell">
      <ScopeNotice />

      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">{t('policiesPage.badge')}</div>
          <p className="eyebrow">{t('policiesPage.eyebrow')}</p>
          <h1>{t('policiesPage.title')}</h1>
          <p className="muted">{t('policiesPage.summary')}</p>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">{t('common.control')}</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>{t('policiesPage.libraryTitle')}</h2>
        <div className="grid">
          {policyItems.map((item) => (
            <article key={item.title} className="assetCard">
              <div className="eyebrow">{t('common.policy')}</div>
              <h3>{item.title}</h3>
              <p className="muted">{item.summary}</p>
              <div className="downloadRow">
                <a className="primaryBtn" href={item.href} download>{t('common.download')}</a>
                <a className="secondaryBtn" href={item.href}>{t('common.open')}</a>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
