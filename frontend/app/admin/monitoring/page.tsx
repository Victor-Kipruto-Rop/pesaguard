'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import PulseLine from '../../../components/PulseLine';
import { apiFetch } from '../../../lib/api';
import { useLocale } from '../../../lib/i18n';

export default function AdminMonitoringPage() {
  const { t } = useLocale();
  const [metrics, setMetrics] = useState<Record<string, number>>({});

  useEffect(() => {
    void apiFetch<Record<string, number>>('/metrics').then((res) => setMetrics(res.data || {}));
    const timer = window.setInterval(() => {
      void apiFetch<Record<string, number>>('/metrics').then((res) => setMetrics(res.data || {}));
    }, 10000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.monitoringEyebrow')} title={t('admin.monitoringTitle')} summary={t('admin.monitoringSummary')} />
      <section className="card">
        <PulseLine height={36} />
        <div className="grid">
          <article className="metricCard card"><div className="label">{t('admin.queueDepth')}</div><div className="value">{metrics.open_count ?? 0}</div></article>
          <article className="metricCard card"><div className="label">{t('admin.errorRate')}</div><div className="value">{((metrics.discrepancy_rate || 0) * 100).toFixed(2)}%</div></article>
          <article className="metricCard card"><div className="label">{t('dashboard.metrics.latencyP95')}</div><div className="value">{metrics.reconciliation_latency_p95 ?? 0}s</div></article>
          <article className="metricCard card"><div className="label">{t('dashboard.metrics.tpm')}</div><div className="value">{metrics.transactions_per_minute ?? 0}</div></article>
        </div>
      </section>
    </main>
  );
}
