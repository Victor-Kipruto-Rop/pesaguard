'use client';

import { useEffect, useMemo, useState } from 'react';
import EmptyState from '../../components/EmptyState';
import LoadingState from '../../components/LoadingState';
import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';
import { formatKeCurrency, formatKeDate } from '../../lib/formatting';

interface ActivityItem {
  id: string;
  event: string;
  message: string;
  severity: string;
  timestamp?: string;
  trans_id: string;
}

interface Discrepancy {
  id: string;
  trans_id: string;
  anomaly_type: string;
  status: string;
  severity: string;
  detected_at: string;
  amount?: number;
}

export default function TransactionsPage() {
  const { t, locale } = useLocale();
  const [items, setItems] = useState<Discrepancy[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<Discrepancy | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [discRes, actRes] = await Promise.all([
        apiFetch<{ items: Discrepancy[] }>('/discrepancies?per_page=50'),
        apiFetch<{ items: ActivityItem[] }>('/activity-feed?limit=20'),
      ]);
      setItems(discRes.data?.items || []);
      setActivity(actRes.data?.items || []);
      setLoading(false);
    };
    void load();
  }, []);

  const rows = useMemo(() => {
    const merged = items.map((item) => ({
      ...item,
      event: activity.find((a) => a.trans_id === item.trans_id)?.event || 'transaction_observed',
    }));
    if (!q.trim()) return merged;
    const needle = q.toLowerCase();
    return merged.filter((item) => item.trans_id.toLowerCase().includes(needle) || item.anomaly_type.toLowerCase().includes(needle));
  }, [items, activity, q]);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('transactions.eyebrow')} title={t('transactions.title')} summary={t('transactions.summary')} />

      <section className="card">
        <div className="toolbar">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('transactions.search')} />
        </div>
        {loading ? (
          <LoadingState message={t('common.loading')} />
        ) : rows.length === 0 ? (
          <EmptyState
            title={t('transactions.emptyTitle')}
            message={t('transactions.emptyMessage')}
            action={<a className="primaryBtn" href="/onboarding">{t('transactions.emptyAction')}</a>}
          />
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{t('dashboard.operations.table.transaction')}</th>
                  <th>{t('transactions.type')}</th>
                  <th>{t('dashboard.operations.table.status')}</th>
                  <th>{t('dashboard.operations.table.severity')}</th>
                  <th>{t('dashboard.operations.table.detected')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.id} onClick={() => setSelected(item)}>
                    <td className="mono">{item.trans_id}</td>
                    <td>{item.anomaly_type}</td>
                    <td><span className="pill ok">{item.status}</span></td>
                    <td><span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span></td>
                    <td>{formatKeDate(item.detected_at, locale as 'en' | 'sw')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selected ? (
        <section className="detailDrawer">
          <div className="sectionTitle">{t('transactions.detailTitle')}</div>
          <div className="detailGrid">
            <div className="detailRow"><span>ID</span><strong className="mono">{selected.trans_id}</strong></div>
            <div className="detailRow"><span>{t('dashboard.operations.table.anomaly')}</span><strong>{selected.anomaly_type}</strong></div>
            <div className="detailRow"><span>{t('dashboard.operations.table.status')}</span><strong>{selected.status}</strong></div>
            <div className="detailRow"><span>{t('transactions.amount')}</span><strong className="mono">{formatKeCurrency(selected.amount || 0)}</strong></div>
          </div>
        </section>
      ) : null}
    </main>
  );
}
