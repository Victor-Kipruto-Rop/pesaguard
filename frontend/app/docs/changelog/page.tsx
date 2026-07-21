'use client';

import DocsNav from '../../../components/DocsNav';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const ENTRIES = [
  { version: '0.9.0-pilot', date: '2026-07-01', items: ['Dashboard, anomalies, and notifications settings', 'English and Kiswahili customer docs', 'Pilot onboarding wizard'] },
  { version: '0.8.0-pilot', date: '2026-06-01', items: ['Localized alert templates', 'Security & trust page', 'Audit log export'] },
];

export default function ChangelogPage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.changelog')} summary={t('docs.changelogSummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="stackList">
          {ENTRIES.map((entry) => (
            <article key={entry.version} className="card">
              <div className="feedHeader">
                <strong className="mono">{entry.version}</strong>
                <span className="muted">{entry.date}</span>
              </div>
              <ul className="stackList">
                {entry.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
