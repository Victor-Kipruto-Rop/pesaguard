'use client';

import { useLocale } from '../../lib/i18n';
import ScopeNotice from '../../components/ScopeNotice';

interface StatusComponent {
  name: string;
  statusKey: string;
  detail: string;
}

interface StatusUpdate {
  title: string;
  message: string;
  time: string;
}

interface StatusHighlight {
  title: string;
  body: string;
}

export default function StatusPage() {
  const { t } = useLocale();
  const components = t<StatusComponent[]>('statusPage.components');
  const updates = t<StatusUpdate[]>('statusPage.updates');
  const highlights = t<StatusHighlight[]>('statusPage.highlights');
  const postureItems = t<string[]>('statusPage.postureItems');

  const statusLabel = (statusKey: string) =>
    statusKey === 'scheduled' ? t('common.scheduled') : t('common.operational');

  return (
    <main className="pageShell">
      <ScopeNotice />

      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">{t('statusPage.badge')}</div>
          <p className="eyebrow">{t('statusPage.eyebrow')}</p>
          <h1>{t('statusPage.title')}</h1>
          <p className="muted">{t('statusPage.summary')}</p>
          <div className="heroActions">
            <a className="primaryBtn" href="/support">{t('statusPage.openSupport')}</a>
            <a className="secondaryBtn" href="/agreements">{t('statusPage.reviewTerms')}</a>
          </div>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">{t('common.signal')}</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="grid twoUp">
        <div className="panel">
          <h2>{t('statusPage.serviceHealth')}</h2>
          <ul className="stackList">
            {components.map((item) => (
              <li key={item.name}>
                <strong>{item.name}</strong>
                <div className="muted" style={{ marginTop: 4 }}>{item.detail}</div>
                <div style={{ marginTop: 8 }}>
                  <span className={`pill ${item.statusKey === 'scheduled' ? 'warning' : 'ok'}`}>
                    {statusLabel(item.statusKey)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>{t('statusPage.operationalPosture')}</h2>
          <ul className="stackList">
            {postureItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel">
        <div className="sectionHeader">
          <h2>{t('statusPage.recentUpdates')}</h2>
          <div className="heroBadge compact">{t('common.live')}</div>
        </div>
        <div className="stackList">
          {updates.map((item) => (
            <div key={item.title} className="feedItem">
              <div className="feedHeader">
                <strong>{item.title}</strong>
                <span className="muted small">{item.time}</span>
              </div>
              <div className="muted">{item.message}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>{t('statusPage.downloadAssets')}</h2>
        <div className="downloadRow">
          <a className="primaryBtn" href="/assets/readiness-pack-summary.txt" download>{t('statusPage.downloadSummary')}</a>
          <a className="secondaryBtn" href="/assets/support-readiness-brief.txt" download>{t('statusPage.downloadBrief')}</a>
        </div>
      </section>
    </main>
  );
}
