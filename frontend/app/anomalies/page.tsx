'use client';

import { useEffect, useState } from 'react';
import EmptyState from '../../components/EmptyState';
import IncidentDetailView from '../../components/IncidentDetailView';
import LoadingState from '../../components/LoadingState';
import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';
import { formatKeDate } from '../../lib/formatting';

interface Discrepancy {
  id: string;
  trans_id: string;
  anomaly_type: string;
  status: string;
  severity: string;
  resolved: boolean;
  detected_at: string;
  assignee?: string;
  notes?: string;
  timeline?: Array<{ ts: string; event: string; message: string }>;
}

export default function AnomaliesPage() {
  const { t, locale } = useLocale();
  const [items, setItems] = useState<Discrepancy[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ severity: '', resolved: 'open' });

  const load = async () => {
    setLoading(true);
    const params = new URLSearchParams({ per_page: '30' });
    if (filters.severity) params.set('severity', filters.severity);
    if (filters.resolved) params.set('resolved', filters.resolved);
    const res = await apiFetch<{ items: Discrepancy[] }>(`/discrepancies?${params}`);
    setItems(res.data?.items || []);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, [filters]);

  const selected = items.find((item) => item.id === selectedId) || null;

  const resolve = async (id: string) => {
    await apiFetch(`/discrepancies/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Resolved from anomalies view' }),
    });
    await load();
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('anomalies.eyebrow')} title={t('anomalies.title')} summary={t('anomalies.summary')} />

      <section className="card">
        <div className="toolbar">
          <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
            <option value="">{t('dashboard.operations.allSeverities')}</option>
            <option value="critical">{t('dashboard.operations.severityCritical')}</option>
            <option value="warning">{t('dashboard.operations.severityWarning')}</option>
            <option value="info">{t('dashboard.operations.severityInfo')}</option>
          </select>
          <select value={filters.resolved} onChange={(e) => setFilters({ ...filters, resolved: e.target.value })}>
            <option value="open">{t('dashboard.operations.open')}</option>
            <option value="resolved">{t('dashboard.operations.resolved')}</option>
            <option value="">{t('dashboard.operations.all')}</option>
          </select>
        </div>

        {loading ? (
          <LoadingState />
        ) : items.length === 0 ? (
          <EmptyState title={t('anomalies.emptyTitle')} message={t('anomalies.emptyMessage')} icon="✓" />
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{t('dashboard.operations.table.transaction')}</th>
                  <th>{t('dashboard.operations.table.anomaly')}</th>
                  <th>{t('dashboard.operations.table.severity')}</th>
                  <th>{t('dashboard.operations.table.detected')}</th>
                  <th>{t('dashboard.operations.table.action')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} onClick={() => setSelectedId(item.id)}>
                    <td className="mono">{item.trans_id}</td>
                    <td>{item.anomaly_type}</td>
                    <td><span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span></td>
                    <td>{formatKeDate(item.detected_at, locale as 'en' | 'sw')}</td>
                    <td>
                      {item.resolved ? (
                        <span className="muted">{t('dashboard.operations.table.resolved')}</span>
                      ) : (
                        <button onClick={(e) => { e.stopPropagation(); void resolve(item.id); }}>{t('anomalies.acknowledge')}</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selected ? (
          <IncidentDetailView
            incident={selected}
            onSaveNote={async (note) => {
              await apiFetch(`/discrepancies/${selected.id}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note }),
              });
              await load();
            }}
            onAssign={async (assignee) => {
              await apiFetch(`/discrepancies/${selected.id}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ assignee }),
              });
              await load();
            }}
          />
        ) : null}
      </section>
    </main>
  );
}
