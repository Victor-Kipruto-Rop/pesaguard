'use client';

import DocsNav from '../../components/DocsNav';
import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

export default function DocsHomePage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.title')} summary={t('docs.summary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card">
          <div className="sectionTitle">{t('docs.sectionsTitle')}</div>
          <ul className="stackList">
            {t<{ title: string; body: string; href: string }[]>('docs.sections').map((section) => (
              <li key={section.href}>
                <strong>{section.title}</strong>
                <div className="muted">{section.body}</div>
                <a className="secondaryBtn" href={section.href}>{t('common.open')}</a>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
