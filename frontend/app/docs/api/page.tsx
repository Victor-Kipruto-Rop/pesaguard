'use client';

import DocsNav from '../../../components/DocsNav';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function ApiReferencePage() {
  const { t } = useLocale();
  const endpoints = t<{ method: string; path: string; description: string }[]>('docs.apiEndpoints');

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.api')} summary={t('docs.apiSummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card">
          <div className="tableWrap">
            <table>
              <thead><tr><th>{t('docs.method')}</th><th>{t('docs.path')}</th><th>{t('auditLog.detail')}</th></tr></thead>
              <tbody>
                {endpoints.map((endpoint) => (
                  <tr key={endpoint.path + endpoint.method}>
                    <td><span className="pill ok">{endpoint.method}</span></td>
                    <td className="mono">{endpoint.path}</td>
                    <td>{endpoint.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
