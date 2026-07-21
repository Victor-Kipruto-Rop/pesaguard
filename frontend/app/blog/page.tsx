'use client';

import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

const POSTS = [
  { title: 'PesaGuard pilot launch', date: '2026-03-01', summary: 'We opened the first live pilot for SACCO reconciliation monitoring.', href: '/docs/changelog' },
  { title: 'Localized alerts in English and Kiswahili', date: '2026-02-15', summary: 'Customer notifications now follow tenant and user locale preferences.', href: '/docs/changelog' },
  { title: 'Daraja webhook hardening', date: '2026-01-20', summary: 'Signature validation, deduplication, and retry-safe ingestion are live.', href: '/security' },
];

export default function BlogPage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('blog.eyebrow')} title={t('blog.title')} summary={t('blog.summary')} />
      <section className="stackList">
        {POSTS.map((post) => (
          <article key={post.title} className="card">
            <div className="muted small">{post.date}</div>
            <h3>{post.title}</h3>
            <p className="muted">{post.summary}</p>
            <a className="secondaryBtn" href={post.href}>{t('blog.readMore')}</a>
          </article>
        ))}
      </section>
    </main>
  );
}
