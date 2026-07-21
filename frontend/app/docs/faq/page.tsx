'use client';

import DocsNav from '../../../components/DocsNav';
import MarkdownDoc from '../../../components/MarkdownDoc';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function FaqDocPage() {
  const { locale, t } = useLocale();
  const src = locale === 'sw' ? '/docs/customer/FAQ_sw.md' : '/docs/customer/FAQ_en.md';

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.faq')} summary={t('docs.faqSummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card"><MarkdownDoc src={src} /></section>
      </div>
    </main>
  );
}
