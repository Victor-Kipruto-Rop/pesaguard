'use client';

import { useEffect, useState } from 'react';
import PulseLine from '../../components/PulseLine';
import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';

export default function HealthPage() {
  const { t } = useLocale();
  const [health, setHealth] = useState<{ status?: string } | null>(null);
  const [metrics, setMetrics] = useState<{ transactions_per_minute?: number; reconciliation_latency_p95?: number } | null>(null);
  const [lastSync, setLastSync] = useState<string>(new Date().toISOString());

  useEffect(() => {
    const load = async () => {
      const [h, m] = await Promise.all([
        apiFetch<{ status: string }>('/health'),
        apiFetch<{ transactions_per_minute: number; reconciliation_latency_p95: number }>('/metrics'),
      ]);
      setHealth(h.data);
      setMetrics(m.data);
      setLastSync(new Date().toISOString());
    };
    void load();
    const timer = window.setInterval(() => void load(), 15000);
    return () => window.clearInterval(timer);
  }, []);

  const online = health?.status === 'ok' || health?.status === 'healthy';

  return (
    <main className="shell">
      <PageHeader eyebrow={t('health.eyebrow')} title={t('health.title')} summary={t('health.summary')} />

      <section className="card">
        <PulseLine height={36} />
        <div className="grid">
          <article className="metricCard card">
            <div className="label">{t('health.uptime')}</div>
            <div className="value">{online ? '99.9%' : '—'}</div>
          </article>
          <article className="metricCard card">
            <div className="label">{t('health.connectivity')}</div>
            <div className="value"><span className={`pill ${online ? 'ok' : 'danger'}`}>{online ? t('health.connected') : t('health.degraded')}</span></div>
          </article>
          <article className="metricCard card">
            <div className="label">{t('health.lastSync')}</div>
            <div className="value mono" style={{ fontSize: '1rem' }}>{new Date(lastSync).toLocaleTimeString()}</div>
          </article>
          <article className="metricCard card">
            <div className="label">{t('dashboard.metrics.tpm')}</div>
            <div className="value">{metrics?.transactions_per_minute ?? '—'}</div>
          </article>
        </div>
      </section>

      <section className="card">
        <div className="sectionTitle">{t('health.componentsTitle')}</div>
        <ul className="stackList">
          {t<{ name: string; detail: string }[]>('statusPage.components').map((item) => (
            <li key={item.name}>
              <strong>{item.name}</strong>
              <div className="muted">{item.detail}</div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
