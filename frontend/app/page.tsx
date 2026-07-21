'use client';

import { useEffect, useMemo, useState } from 'react';
import RoleAwarePanel from '../components/RoleAwarePanel';
import { TrendLineChart } from '../components/Charts';
import IncidentDetailView from '../components/IncidentDetailView';
import { useLocale } from '../lib/i18n';
import { formatKeCurrency, formatKeDate } from '../lib/formatting';


interface Discrepancy {
  id: string;
  trans_id: string;
  anomaly_type: string;
  status: string;
  severity: string;
  resolved: boolean;
  tenant_id?: string;
  assignee?: string;
  notes?: string;
  timeline?: Array<{ ts: string; event: string; message: string }>;
  detected_at: string;
  sla_status?: string;
  sla_remaining_minutes?: number | null;
}

interface Metrics {
  transactions_per_minute: number;
  discrepancy_rate: number;
  reconciliation_latency_p50: number;
  reconciliation_latency_p95: number;
  open_count: number;
  resolved_count: number;
  severity_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  trend_series: number[];
}

interface ActivityItem {
  id: string;
  event: string;
  message: string;
  severity: string;
  timestamp?: string;
  trans_id: string;
}

interface QueueItem {
  id: string;
  trans_id: string;
  severity: string;
  assignee: string;
  queue_status: string;
  anomaly_type: string;
  detected_at?: string;
}

export default function HomePage() {
  const { t, locale, format } = useLocale();
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    transactions_per_minute: 0,
    discrepancy_rate: 0,
    reconciliation_latency_p50: 0,
    reconciliation_latency_p95: 0,
    open_count: 0,
    resolved_count: 0,
    severity_breakdown: {},
    status_breakdown: {},
    trend_series: [],
  });
  const [filters, setFilters] = useState({ status: '', severity: '', resolved: '', q: '' });
  const [loading, setLoading] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(5);
  const [total, setTotal] = useState(0);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([]);
  const [assignmentQueue, setAssignmentQueue] = useState<QueueItem[]>([]);
  const [toast, setToast] = useState('');

  const loadData = async (nextPage = page) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    params.set('page', nextPage.toString());
    params.set('per_page', perPage.toString());
    if (filters.severity) params.set('severity', filters.severity);
    if (filters.resolved) params.set('resolved', filters.resolved);
    if (filters.q) params.set('q', filters.q);

    const [discrepanciesRes, metricsRes, activityRes, queueRes] = await Promise.all([
      fetch(`http://127.0.0.1:5001/discrepancies?${params.toString()}`),
      fetch('http://127.0.0.1:5001/metrics'),
      fetch('http://127.0.0.1:5001/activity-feed?limit=5'),
      fetch('http://127.0.0.1:5001/assignment-queue'),
    ]);
    const discrepancyData = await discrepanciesRes.json();
    const metricsData = await metricsRes.json();
    const activityData = await activityRes.json();
    const queueData = await queueRes.json();
    setDiscrepancies(discrepancyData.items || []);
    setTotal(discrepancyData.total || 0);
    setMetrics(metricsData);
    setActivityFeed(activityData.items || []);
    setAssignmentQueue(queueData.items || []);
    setLoading(false);
  };

  useEffect(() => {
    void loadData(page);
    const timer = setInterval(() => {
      void loadData(page);
    }, 8000);
    return () => clearInterval(timer);
  }, [page, perPage]);

  const resolvedRate = useMemo(() => {
    if (!discrepancies.length) return 0;
    return Math.round((discrepancies.filter((item) => item.resolved).length / discrepancies.length) * 100);
  }, [discrepancies]);

  const selectedIncident = useMemo(() => discrepancies.find((item) => item.id === selectedId) || discrepancies[0] || null, [discrepancies, selectedId]);

  const chartData = useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return (metrics.trend_series || []).map((value, index) => ({
      day: days[index] || `D${index + 1}`,
      value,
      resolved: Math.floor(value * 0.6),
    }));
  }, [metrics.trend_series]);

  const showToast = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2200);
  };


  const handleResolve = async (id: string) => {
    setResolvingId(id);
    const response = await fetch(`http://127.0.0.1:5001/discrepancies/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Resolved from operations console' }),
    });
    if (response.ok) {
      setDiscrepancies((current) => current.map((item) => item.id === id ? { ...item, resolved: true } : item));
      showToast('Incident resolved');
      await loadData(page);
    }
    setResolvingId(null);
  };

  const handleBulkResolve = async () => {
    if (!selectedIds.length) return;
    const response = await fetch('http://127.0.0.1:5001/discrepancies/bulk-resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: selectedIds, note: 'Bulk resolved from operations console' }),
    });
    if (response.ok) {
      setSelectedIds([]);
      showToast('Bulk resolution applied');
      await loadData(page);
    }
  };

  const handleSaveNote = async (note: string) => {
    if (!selectedIncident) return;
    const response = await fetch(`http://127.0.0.1:5001/discrepancies/${selectedIncident.id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note }),
    });
    if (response.ok) {
      showToast('Operator note saved');
      await loadData(page);
    }
  };

  const handleAssign = async (assignee: string) => {
    if (!selectedIncident) return;
    const response = await fetch(`http://127.0.0.1:5001/discrepancies/${selectedIncident.id}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assignee }),
    });
    if (response.ok) {
      showToast('Assignment updated');
      await loadData(page);
    }
  };

  return (
    <main className="shell">
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">PesaGuard Control Center</p>
          <h1>{t('home.heroTitle')}</h1>
          <p className="muted">{t('home.heroSubtitle')}</p>
          <div className="heroActions">
            <a className="primaryBtn" href="#operations">{t('home.heroCtaPrimary')}</a>
            <a className="secondaryBtn" href="/settings">{t('home.heroCtaSecondary')}</a>
          </div>
          <div className="heroMeta">
            {(t<string[]>('home.heroMeta') || []).map((item: string) => (
              <span key={item}>● {item}</span>
            ))}
          </div>
          <div className="heroMeta" style={{ marginTop: 8 }}>
            <span>{t('scope.label')}</span>
          </div>
        </div>
        <div className="heroPanel">
          <div className="heroStat">
            <strong>{metrics.open_count}</strong>
            <span>{t('dashboard.heroStats.openIncidents')}</span>
          </div>
          <div className="heroStat">
            <strong>{metrics.reconciliation_latency_p95}s</strong>
            <span>{t('dashboard.heroStats.latency')}</span>
          </div>
          <div className="heroStat">
            <strong>{metrics.transactions_per_minute}</strong>
            <span>{t('dashboard.heroStats.tpm')}</span>
          </div>
        </div>
      </section>

      <section className="grid">
        <article className="card metricCard">
          <div className="label">{t('dashboard.metrics.tpm')}</div>
          <div className="value">{metrics.transactions_per_minute}</div>
        </article>
        <article className="card metricCard">
          <div className="label">{t('dashboard.metrics.openExceptions')}</div>
          <div className="value">{metrics.open_count}</div>
        </article>
        <article className="card metricCard">
          <div className="label">{t('dashboard.metrics.resolutionRate')}</div>
          <div className="value">{resolvedRate}%</div>
        </article>
        <article className="card metricCard">
          <div className="label">{t('dashboard.metrics.latencyP95')}</div>
          <div className="value">{metrics.reconciliation_latency_p95}s</div>
        </article>
      </section>

      <section className="grid splitGrid">
        <article className="card">
          <TrendLineChart data={chartData} title={t('dashboard.charts.exceptionTrend')} height={260} />
        </article>
        <article className="card">
          <div className="sectionTitle">{t('dashboard.operationalHealth.title')}</div>
          <div className="row"><span>{t('dashboard.operationalHealth.discrepancyRate')}</span><strong>{metrics.discrepancy_rate}</strong></div>
          <div className="row"><span>{t('dashboard.operationalHealth.p50Latency')}</span><strong>{metrics.reconciliation_latency_p50}s</strong></div>
          <div className="row"><span>{t('dashboard.operationalHealth.resolvedToday')}</span><strong>{metrics.resolved_count}</strong></div>
          <div className="row"><span>{t('dashboard.operationalHealth.severityMix')}</span><strong>{Object.entries(metrics.severity_breakdown).length ? Object.entries(metrics.severity_breakdown).map(([key, value]) => `${key}:${value}`).join(' · ') : 'none'}</strong></div>
        </article>
      </section>

      <section className="card trendAnalytics">
        <div className="sectionTitle">{t('dashboard.trends.title')}</div>
        <div className="trendGrid">
          <div className="trendMetric">
            <div className="label">{t('dashboard.trends.avgIncidents')}</div>
            <div className="value">{Math.round((chartData.reduce((sum, d) => sum + d.value, 0) / chartData.length) || 0)}</div>
            <div className="muted small">↓ 12% from previous week</div>
          </div>
          <div className="trendMetric">
            <div className="label">{t('dashboard.trends.peakHour')}</div>
            <div className="value">3:00 PM</div>
            <div className="muted small">{format('dashboard.trends.peakHourHint', { value: Math.round(metrics.transactions_per_minute * 1.4) })}</div>
          </div>
          <div className="trendMetric">
            <div className="label">{t('dashboard.trends.resolutionEfficiency')}</div>
            <div className="value">{resolvedRate}%</div>
            <div className="muted small">↑ 8% this month</div>
          </div>
          <div className="trendMetric">
            <div className="label">{t('dashboard.trends.slaCompliance')}</div>
            <div className="value">92%</div>
            <div className="muted small">Critical incidents only</div>
          </div>
        </div>
      </section>

      <RoleAwarePanel />

      <section className="grid splitGrid">
        <article className="card">
          <div className="sectionTitle">{t('dashboard.activityFeed.title')}</div>
          <div className="feedList">
            {activityFeed.map((item) => (
              <div key={item.id} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.event}</strong>
                  <span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span>
                </div>
                <div className="muted">{item.message}</div>
                <div className="muted small">{item.trans_id} • {formatKeDate(item.timestamp, locale as 'en' | 'sw') || t('dashboard.activityFeed.pending')}</div>
              </div>
            ))}
          </div>
        </article>
        <article className="card">
          <div className="sectionTitle">{t('dashboard.assignmentQueue.title')}</div>
          <div className="feedList">
            {assignmentQueue.map((item) => (
              <div key={item.id} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.trans_id}</strong>
                  <span className={`pill ${item.queue_status === 'needs_assignment' ? 'warning' : 'ok'}`}>{item.queue_status}</span>
                </div>
                <div className="muted">{item.anomaly_type}</div>
                <div className="muted small">{t('dashboard.assignmentQueue.assignee')} {item.assignee}</div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card" id="operations">
        <div className="sectionTitle">{t('dashboard.operations.title')}</div>
        <div className="toolbar">
          <input
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder={t('dashboard.operations.searchPlaceholder')}
          />
          <select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
            <option value="">{t('dashboard.operations.allAnomalies')}</option>
            <option value="missing_payment">{t('dashboard.operations.statusMissingPayment')}</option>
            <option value="needs_review">{t('dashboard.operations.statusNeedsReview')}</option>
            <option value="duplicate">{t('dashboard.operations.statusDuplicate')}</option>
          </select>
          <select value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}>
            <option value="">{t('dashboard.operations.allSeverities')}</option>
            <option value="critical">{t('dashboard.operations.severityCritical')}</option>
            <option value="warning">{t('dashboard.operations.severityWarning')}</option>
            <option value="info">{t('dashboard.operations.severityInfo')}</option>
          </select>
          <select value={filters.resolved} onChange={(event) => setFilters((current) => ({ ...current, resolved: event.target.value }))}>
            <option value="">{t('dashboard.operations.all')}</option>
            <option value="open">{t('dashboard.operations.open')}</option>
            <option value="resolved">{t('dashboard.operations.resolved')}</option>
          </select>
          <button onClick={() => { setPage(1); void loadData(1); }}>{loading ? t('dashboard.operations.refreshing') : t('dashboard.operations.apply')}</button>
        </div>
        <div className="bulkRow">
          <button onClick={() => void handleBulkResolve()} disabled={!selectedIds.length}>{t('dashboard.operations.bulkResolve')}</button>
          <span className="muted">{selectedIds.length} {t('dashboard.operations.selected')}</span>
          <select value={perPage} onChange={(event) => { setPerPage(Number(event.target.value)); setPage(1); }}>
            <option value={5}>5 {t('dashboard.operations.perPage')}</option>
            <option value={10}>10 {t('dashboard.operations.perPage')}</option>
            <option value={20}>20 {t('dashboard.operations.perPage')}</option>
          </select>
        </div>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" checked={selectedIds.length > 0 && selectedIds.length === discrepancies.length} onChange={() => setSelectedIds(selectedIds.length === discrepancies.length ? [] : discrepancies.map((item) => item.id))} /></th>
                <th>{t('dashboard.operations.table.transaction')}</th>
                <th>{t('dashboard.operations.table.anomaly')}</th>
                <th>{t('dashboard.operations.table.status')}</th>
                <th>{t('dashboard.operations.table.severity')}</th>
                <th>{t('dashboard.operations.table.sla')}</th>
                <th>{t('dashboard.operations.table.detected')}</th>
                <th>{t('dashboard.operations.table.action')}</th>
              </tr>
            </thead>
            <tbody>
              {discrepancies.map((item) => (
                <tr key={item.id} onClick={() => setSelectedId(item.id)}>
                  <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => setSelectedIds((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current, item.id])} /></td>
                  <td>{item.trans_id}</td>
                  <td>{item.anomaly_type}</td>
                  <td><span className={`pill ${item.resolved ? 'ok' : item.status === 'needs_review' ? 'warning' : 'danger'}`}>{item.resolved ? t('dashboard.operations.table.resolved') : item.status}</span></td>
                  <td><span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span></td>
                  <td>
                    {item.severity === 'critical' ? (
                      <span className={`pill ${item.sla_status === 'breaching' ? 'danger' : item.sla_status === 'warning' ? 'warning' : 'ok'}`}>
                        {item.sla_status === 'breaching' ? `${t('dashboard.operations.table.slaBreaching')} • ${item.sla_remaining_minutes}m` : item.sla_status === 'warning' ? `${t('dashboard.operations.table.slaWarning')} • ${item.sla_remaining_minutes}m` : t('dashboard.operations.table.slaOnTrack')}
                      </span>
                    ) : <span className="muted">{t('dashboard.operations.table.notApplicable')}</span>}
                  </td>
                  <td>{formatKeDate(item.detected_at, locale as 'en' | 'sw')}</td>
                  <td>
                    {item.resolved ? (
                      <span className="muted">{t('dashboard.operations.table.resolved')}</span>
                    ) : (
                      <button onClick={() => void handleResolve(item.id)} disabled={resolvingId === item.id}>
                        {resolvingId === item.id ? t('dashboard.operations.table.resolving') : t('dashboard.operations.table.resolve')}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="paginationRow">
          <button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>{t('dashboard.operations.pagination.previous')}</button>
          <span className="muted">{t('dashboard.operations.pagination.page')} {page} {t('dashboard.operations.pagination.of')} {Math.max(1, Math.ceil(total / perPage))}</span>
          <button disabled={page * perPage >= total} onClick={() => setPage((current) => current + 1)}>{t('dashboard.operations.pagination.next')}</button>
        </div>
        {selectedIncident && (
          <IncidentDetailView
            incident={selectedIncident}
            onSaveNote={handleSaveNote}
            onAssign={handleAssign}
          />
        )}
      </section>
      {toast ? <div className="toast">{toast}</div> : null}
    </main>
  );
}
