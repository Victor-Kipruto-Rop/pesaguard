'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';
import { adminFetch } from '../../../lib/adminApi';

interface MonitoringSummary {
  status: string;
  uptime: number;
  open_incidents: number;
  avg_latency_ms: number;
}

export default function TenantMonitoringPage() {
  const { t } = useLocale();
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSummary = async () => {
      const response = await adminFetch<MonitoringSummary>('/metrics');
      if (response.ok && response.data) {
        setSummary(response.data);
      } else if (response.status === 403) {
        setError('Admin access token is invalid. Please update it in Settings.');
      } else {
        setError('Unable to load monitoring summary.');
      }
    };

    void loadSummary();
  }, []);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.customersEyebrow')} title="Tenant monitoring" summary="Track service health and system availability for this tenant." />

      {error ? (
        <section className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </section>
      ) : null}

      <section className="card">
        <div className="sectionTitle">Current status</div>
        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <div><strong>Status</strong>: {summary?.status ?? 'unknown'}</div>
          <div><strong>Uptime</strong>: {summary?.uptime ?? 0}%</div>
          <div><strong>Open incidents</strong>: {summary?.open_incidents ?? 0}</div>
          <div><strong>Average latency</strong>: {summary?.avg_latency_ms ?? 0} ms</div>
        </div>
      </section>
    </main>
  );
}
