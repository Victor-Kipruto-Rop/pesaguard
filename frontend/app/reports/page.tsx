'use client';

import { useState } from 'react';
import LoadingState from '../../components/LoadingState';
import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';

interface ReportData {
  total_incidents?: number;
  resolved?: number;
  open?: number;
  resolution_rate?: number;
  sla_compliance?: number;
}

export default function ReportsPage() {
  const { t } = useLocale();
  const [days, setDays] = useState(7);
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    const res = await apiFetch<ReportData>(`/analytics/reconciliation-report?days=${days}`);
    setReport(res.data);
    setLoading(false);
  };

  const exportCsv = () => {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001'}/discrepancies/export/csv`, '_blank');
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('reports.eyebrow')} title={t('reports.title')} summary={t('reports.summary')} />

      <section className="card">
        <div className="toolbar">
          <label className="muted">{t('toolsPage.reportPeriod')}</label>
          <input type="number" min={1} max={90} value={days} onChange={(e) => setDays(Number(e.target.value))} />
          <button onClick={() => void generate()} disabled={loading}>{loading ? t('toolsPage.generating') : t('toolsPage.generateReport')}</button>
          <button className="secondaryBtn" onClick={exportCsv}>{t('toolsPage.downloadCsv')}</button>
        </div>

        {loading ? <LoadingState /> : report ? (
          <div className="grid">
            <article className="metricCard card"><div className="label">{t('toolsPage.totalIncidents')}</div><div className="value">{report.total_incidents ?? 0}</div></article>
            <article className="metricCard card"><div className="label">{t('toolsPage.resolved')}</div><div className="value">{report.resolved ?? 0}</div></article>
            <article className="metricCard card"><div className="label">{t('toolsPage.open')}</div><div className="value">{report.open ?? 0}</div></article>
            <article className="metricCard card"><div className="label">{t('toolsPage.resolutionRate')}</div><div className="value">{Math.round((report.resolution_rate || 0) * 100)}%</div></article>
          </div>
        ) : (
          <p className="muted">{t('reports.empty')}</p>
        )}
      </section>

      <section className="card">
        <div className="sectionTitle">{t('reports.scheduledTitle')}</div>
        <p className="muted">{t('reports.scheduledBody')}</p>
        <div className="formRow" style={{ maxWidth: 360, marginTop: 12 }}>
          <select defaultValue="weekly">
            <option value="daily">{t('reports.daily')}</option>
            <option value="weekly">{t('reports.weekly')}</option>
            <option value="monthly">{t('reports.monthly')}</option>
          </select>
        </div>
      </section>
    </main>
  );
}
