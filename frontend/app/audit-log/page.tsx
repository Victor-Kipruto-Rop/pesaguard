'use client';

import { useEffect, useState } from 'react';
import EmptyState from '../../components/EmptyState';
import LoadingState from '../../components/LoadingState';
import PageHeader from '../../components/PageHeader';
import { apiFetch } from '../../lib/api';
import { useLocale } from '../../lib/i18n';

interface AuditEntry {
  id: string;
  action: string;
  actor: string;
  timestamp: string;
  detail: string;
}

export default function AuditLogPage() {
  const { t } = useLocale();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const act = await apiFetch<{ items: Array<{ id: string; event: string; message: string; timestamp?: string }> }>('/activity-feed?limit=50');
      const mapped = (act.data?.items || []).map((item, index) => ({
        id: item.id || String(index),
        action: item.event,
        actor: 'system',
        timestamp: item.timestamp || new Date().toISOString(),
        detail: item.message,
      }));
      setEntries(mapped);
      setLoading(false);
    };
    void load();
  }, []);

  const filtered = entries.filter((entry) => {
    if (!q.trim()) return true;
    const needle = q.toLowerCase();
    return entry.action.toLowerCase().includes(needle) || entry.detail.toLowerCase().includes(needle);
  });

  const exportLog = () => {
    const csv = ['action,actor,timestamp,detail', ...filtered.map((e) => `"${e.action}","${e.actor}","${e.timestamp}","${e.detail.replace(/"/g, '""')}"`)].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pesaguard-audit-log.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('auditLog.eyebrow')} title={t('auditLog.title')} summary={t('auditLog.summary')} />

      <section className="card">
        <div className="toolbar">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('auditLog.search')} />
          <button onClick={exportLog}>{t('auditLog.export')}</button>
        </div>
        {loading ? (
          <LoadingState />
        ) : filtered.length === 0 ? (
          <EmptyState title={t('auditLog.emptyTitle')} message={t('auditLog.emptyMessage')} />
        ) : (
          <div className="tableWrap">
            <table>
              <thead><tr><th>{t('auditLog.action')}</th><th>{t('auditLog.actor')}</th><th>{t('auditLog.time')}</th><th>{t('auditLog.detail')}</th></tr></thead>
              <tbody>
                {filtered.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.action}</td>
                    <td>{entry.actor}</td>
                    <td className="mono">{new Date(entry.timestamp).toLocaleString()}</td>
                    <td>{entry.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
