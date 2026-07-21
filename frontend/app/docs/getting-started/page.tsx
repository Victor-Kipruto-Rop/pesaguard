'use client';

import DocsNav from '../../../components/DocsNav';
import MarkdownDoc from '../../../components/MarkdownDoc';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function GettingStartedDocPage() {
  const { locale, t } = useLocale();
  const src = locale === 'sw' ? '/docs/customer/GETTING_STARTED_sw.md' : '/docs/customer/GETTING_STARTED_en.md';

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.gettingStarted')} summary={t('docs.gettingStartedSummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card"><MarkdownDoc src={src} /></section>
      </div>
    </main>
  );
}
