'use client';

import DocsNav from '../../../components/DocsNav';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function GlossaryPage() {
  const { t } = useLocale();
  const terms = t<{ term: string; definition: string }[]>('docs.glossaryTerms');

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.glossary')} summary={t('docs.glossarySummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card">
          {terms.map((item) => (
            <div key={item.term} className="row" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <strong>{item.term}</strong>
              <span className="muted">{item.definition}</span>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
