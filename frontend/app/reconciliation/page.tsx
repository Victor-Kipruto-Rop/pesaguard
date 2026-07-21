'use client';

import { useEffect, useState } from 'react';
import EmptyState from '../../components/EmptyState';
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
}

export default function ReconciliationPage() {
  const { t, locale } = useLocale();
  const [unmatched, setUnmatched] = useState<Discrepancy[]>([]);
  const [suggestions, setSuggestions] = useState<Discrepancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');

  const load = async () => {
    setLoading(true);
    const res = await apiFetch<{ items: Discrepancy[] }>('/discrepancies?resolved=open&per_page=50');
    const items = res.data?.items || [];
    setUnmatched(items.filter((item) => item.status === 'missing_payment' || item.status === 'needs_review'));
    setSuggestions(items.filter((item) => item.status === 'duplicate'));
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  const match = async (id: string) => {
    const res = await apiFetch(`/discrepancies/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Manual match from reconciliation view' }),
    });
    if (res.ok) {
      setToast(t('reconciliation.matched'));
      await load();
      window.setTimeout(() => setToast(''), 2200);
    }
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('reconciliation.eyebrow')} title={t('reconciliation.title')} summary={t('reconciliation.summary')} />

      {loading ? (
        <LoadingState />
      ) : unmatched.length === 0 && suggestions.length === 0 ? (
        <EmptyState title={t('reconciliation.emptyTitle')} message={t('reconciliation.emptyMessage')} icon="✓" />
      ) : (
        <section className="grid twoUp">
          <article className="card">
            <div className="sectionTitle">{t('reconciliation.unmatched')}</div>
            {unmatched.length === 0 ? (
              <p className="muted">{t('reconciliation.noUnmatched')}</p>
            ) : (
              <div className="feedList">
                {unmatched.map((item) => (
                  <div key={item.id} className="feedItem">
                    <div className="feedHeader">
                      <strong className="mono">{item.trans_id}</strong>
                      <span className={`pill ${item.severity === 'critical' ? 'danger' : 'warning'}`}>{item.severity}</span>
                    </div>
                    <div className="muted">{item.anomaly_type} · {formatKeDate(item.detected_at, locale as 'en' | 'sw')}</div>
                    <button style={{ marginTop: 8 }} onClick={() => void match(item.id)}>{t('reconciliation.match')}</button>
                  </div>
                ))}
              </div>
            )}
          </article>
          <article className="card">
            <div className="sectionTitle">{t('reconciliation.suggested')}</div>
            {suggestions.length === 0 ? (
              <p className="muted">{t('reconciliation.noSuggested')}</p>
            ) : (
              <div className="feedList">
                {suggestions.map((item) => (
                  <div key={item.id} className="feedItem">
                    <div className="feedHeader">
                      <strong className="mono">{item.trans_id}</strong>
                      <span className="pill ok">{t('reconciliation.suggestedLabel')}</span>
                    </div>
                    <div className="muted">{item.anomaly_type}</div>
                    <button style={{ marginTop: 8 }} onClick={() => void match(item.id)}>{t('reconciliation.confirmMatch')}</button>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>
      )}
      {toast ? <div className="toast">{toast}</div> : null}
    </main>
  );
}
