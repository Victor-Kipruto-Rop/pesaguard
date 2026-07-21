'use client';

import DocsNav from '../../../components/DocsNav';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function WebhooksDocPage() {
  const { t } = useLocale();

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('docs.eyebrow')} title={t('docs.webhooks')} summary={t('docs.webhooksSummary')} />
      <div className="docsLayout">
        <DocsNav />
        <section className="card">
          <div className="sectionTitle">{t('docs.payloadTitle')}</div>
          <pre className="mono detailDrawer">{`{
  "trans_id": "QHX1234567",
  "amount": 1500,
  "msisdn": "2547XXXXXXXX",
  "timestamp": "2026-07-15T10:22:11Z"
}`}</pre>
          <div className="sectionTitle">{t('docs.retryTitle')}</div>
          <p className="muted">{t('docs.retryBody')}</p>
          <div className="sectionTitle">{t('docs.signatureTitle')}</div>
          <p className="muted">{t('docs.signatureBody')}</p>
        </section>
      </div>
    </main>
  );
}
