'use client';

import { useLocale } from '../../lib/i18n';
import ScopeNotice from '../../components/ScopeNotice';
import OnboardingLinks from '../../components/OnboardingLinks';

interface SupportChannel {
  label: string;
  value: string;
  detail: string;
}

interface SlaLevel {
  title: string;
  target: string;
  detail: string;
}

interface SupportHighlight {
  title: string;
  body: string;
}

export default function SupportPage() {
  const { t } = useLocale();
  const supportChannels = t<SupportChannel[]>('supportPage.channels');
  const slaLevels = t<SlaLevel[]>('supportPage.slaLevels');
  const highlights = t<SupportHighlight[]>('supportPage.highlights');
  const reportItems = t<string[]>('supportPage.reportItems');

  return (
    <main className="pageShell">
      <ScopeNotice />

      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">{t('supportPage.badge')}</div>
          <p className="eyebrow">{t('supportPage.eyebrow')}</p>
          <h1>{t('supportPage.title')}</h1>
          <p className="muted">{t('supportPage.summary')}</p>
          <div className="heroActions">
            <a className="primaryBtn" href="mailto:pilot-support@pesaguard.example">{t('supportPage.emailSupport')}</a>
            <a className="secondaryBtn" href="/status">{t('supportPage.viewStatus')}</a>
          </div>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">{t('supportPage.promise')}</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="grid twoUp">
        <div className="panel">
          <h2>{t('supportPage.channelsTitle')}</h2>
          <div className="stackList">
            {supportChannels.map((item) => (
              <div key={item.label} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.label}</strong>
                </div>
                <div className="muted" style={{ marginBottom: 4 }}>{item.value}</div>
                <div className="muted">{item.detail}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          <h2>{t('supportPage.reportTitle')}</h2>
          <ul className="stackList">
            {reportItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel">
        <h2>{t('supportPage.responseTargets')}</h2>
        <div className="grid">
          {slaLevels.map((item) => (
            <div key={item.title} className="panel">
              <div className="eyebrow">{item.title}</div>
              <h3>{item.target}</h3>
              <div className="muted">{item.detail}</div>
            </div>
          ))}
        </div>
      </section>

      <OnboardingLinks />

      <section className="panel">
        <h2>{t('supportPage.downloadAssets')}</h2>
        <div className="downloadRow">
          <a className="primaryBtn" href="/assets/support-readiness-brief.txt" download>{t('supportPage.downloadBrief')}</a>
          <a className="secondaryBtn" href="/assets/readiness-pack-summary.txt" download>{t('supportPage.downloadSummary')}</a>
        </div>
      </section>
    </main>
  );
}
