'use client';

import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useEffect, useState } from 'react';
import { useLocale } from '../../lib/i18n';

export default function AdminDashboardPage() {
  const { t } = useLocale();
  const [metrics, setMetrics] = useState<{ open_count?: number; transactions_per_minute?: number } | null>(null);

  useEffect(() => {
    void apiFetch('/metrics').then((res) => setMetrics(res.data as typeof metrics));
  }, []);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.eyebrow')} title={t('admin.title')} summary={t('admin.summary')} />
      <section className="grid">
        <article className="metricCard card"><div className="label">{t('admin.customersLive')}</div><div className="value">1</div></article>
        <article className="metricCard card"><div className="label">{t('admin.pilotActive')}</div><div className="value">1</div></article>
        <article className="metricCard card"><div className="label">{t('dashboard.metrics.openExceptions')}</div><div className="value">{metrics?.open_count ?? '—'}</div></article>
        <article className="metricCard card"><div className="label">{t('dashboard.metrics.tpm')}</div><div className="value">{metrics?.transactions_per_minute ?? '—'}</div></article>
      </section>
      <section className="card">
        <div className="sectionTitle">{t('admin.systemHealth')}</div>
        <p className="muted">{t('admin.systemHealthBody')}</p>
        <a className="secondaryBtn" href="/admin/monitoring">{t('admin.viewMonitoring')}</a>
      </section>
    </main>
  );
}
