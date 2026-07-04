'use client';

import { useEffect, useMemo, useState } from 'react';
import RoleAwarePanel from '../components/RoleAwarePanel';
import { TrendLineChart } from '../components/Charts';
import IncidentDetailView from '../components/IncidentDetailView';


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
          <h1>Modern reconciliation operations for every tenant</h1>
          <p className="muted">Monitor exceptions, resolve incidents, and keep payment flows trusted in real time with a premium operator experience.</p>
          <div className="heroActions">
            <a className="primaryBtn" href="#operations">Open operations queue</a>
            <a className="secondaryBtn" href="/settings">Review alert routing</a>
          </div>
          <div className="heroMeta">
            <span>● Live anomaly stream</span>
            <span>● SLA-aware escalations</span>
            <span>● Audit-ready workflow</span>
          </div>
        </div>
        <div className="heroPanel">
          <div className="heroStat">
            <strong>{metrics.open_count}</strong>
            <span>Open incidents in queue</span>
          </div>
          <div className="heroStat">
            <strong>{metrics.reconciliation_latency_p95}s</strong>
            <span>Median resolution latency</span>
          </div>
          <div className="heroStat">
            <strong>{metrics.transactions_per_minute}</strong>
            <span>Transactions per minute</span>
          </div>
        </div>
      </section>

      <section className="grid">
        <article className="card metricCard">
          <div className="label">Transactions / min</div>
          <div className="value">{metrics.transactions_per_minute}</div>
        </article>
        <article className="card metricCard">
          <div className="label">Open Exceptions</div>
          <div className="value">{metrics.open_count}</div>
        </article>
        <article className="card metricCard">
          <div className="label">Resolution Rate</div>
          <div className="value">{resolvedRate}%</div>
        </article>
        <article className="card metricCard">
          <div className="label">Latency p95</div>
          <div className="value">{metrics.reconciliation_latency_p95}s</div>
        </article>
      </section>

      <section className="grid splitGrid">
        <article className="card">
          <TrendLineChart data={chartData} title="Exception trend (7 days)" height={260} />
        </article>
        <article className="card">
          <div className="sectionTitle">Operational health</div>
          <div className="row"><span>Discrepancy rate</span><strong>{metrics.discrepancy_rate}</strong></div>
          <div className="row"><span>p50 latency</span><strong>{metrics.reconciliation_latency_p50}s</strong></div>
          <div className="row"><span>Resolved today</span><strong>{metrics.resolved_count}</strong></div>
          <div className="row"><span>Severity mix</span><strong>{Object.entries(metrics.severity_breakdown).length ? Object.entries(metrics.severity_breakdown).map(([key, value]) => `${key}:${value}`).join(' · ') : 'none'}</strong></div>
        </article>
      </section>

      <RoleAwarePanel />

      <section className="grid splitGrid">
        <article className="card">
          <div className="sectionTitle">Recent activity feed</div>
          <div className="feedList">
            {activityFeed.map((item) => (
              <div key={item.id} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.event}</strong>
                  <span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span>
                </div>
                <div className="muted">{item.message}</div>
                <div className="muted small">{item.trans_id} • {item.timestamp || 'pending'}</div>
              </div>
            ))}
          </div>
        </article>
        <article className="card">
          <div className="sectionTitle">Assignment queue</div>
          <div className="feedList">
            {assignmentQueue.map((item) => (
              <div key={item.id} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.trans_id}</strong>
                  <span className={`pill ${item.queue_status === 'needs_assignment' ? 'warning' : 'ok'}`}>{item.queue_status}</span>
                </div>
                <div className="muted">{item.anomaly_type}</div>
                <div className="muted small">Assignee: {item.assignee}</div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card" id="operations">
        <div className="sectionTitle">Tenant operations</div>
        <div className="toolbar">
          <input
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder="Search transaction or anomaly"
          />
          <select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
            <option value="">All anomalies</option>
            <option value="missing_payment">Missing payment</option>
            <option value="needs_review">Needs review</option>
            <option value="duplicate">Duplicate</option>
          </select>
          <select value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
          <select value={filters.resolved} onChange={(event) => setFilters((current) => ({ ...current, resolved: event.target.value }))}>
            <option value="">All</option>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
          </select>
          <button onClick={() => { setPage(1); void loadData(1); }}>{loading ? 'Refreshing…' : 'Apply'}</button>
        </div>
        <div className="bulkRow">
          <button onClick={() => void handleBulkResolve()} disabled={!selectedIds.length}>Bulk resolve selected</button>
          <span className="muted">{selectedIds.length} selected</span>
          <select value={perPage} onChange={(event) => { setPerPage(Number(event.target.value)); setPage(1); }}>
            <option value={5}>5 per page</option>
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
          </select>
        </div>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th><input type="checkbox" checked={selectedIds.length > 0 && selectedIds.length === discrepancies.length} onChange={() => setSelectedIds(selectedIds.length === discrepancies.length ? [] : discrepancies.map((item) => item.id))} /></th>
                <th>Transaction</th>
                <th>Anomaly</th>
                <th>Status</th>
                <th>Severity</th>
                <th>SLA</th>
                <th>Detected</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {discrepancies.map((item) => (
                <tr key={item.id} onClick={() => setSelectedId(item.id)}>
                  <td><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => setSelectedIds((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current, item.id])} /></td>
                  <td>{item.trans_id}</td>
                  <td>{item.anomaly_type}</td>
                  <td><span className={`pill ${item.resolved ? 'ok' : item.status === 'needs_review' ? 'warning' : 'danger'}`}>{item.resolved ? 'resolved' : item.status}</span></td>
                  <td><span className={`pill ${item.severity === 'critical' ? 'danger' : item.severity === 'warning' ? 'warning' : 'ok'}`}>{item.severity}</span></td>
                  <td>
                    {item.severity === 'critical' ? (
                      <span className={`pill ${item.sla_status === 'breaching' ? 'danger' : item.sla_status === 'warning' ? 'warning' : 'ok'}`}>
                        {item.sla_status === 'breaching' ? `breaching • ${item.sla_remaining_minutes}m` : item.sla_status === 'warning' ? `warning • ${item.sla_remaining_minutes}m` : 'on track'}
                      </span>
                    ) : <span className="muted">n/a</span>}
                  </td>
                  <td>{item.detected_at}</td>
                  <td>
                    {item.resolved ? (
                      <span className="muted">Resolved</span>
                    ) : (
                      <button onClick={() => void handleResolve(item.id)} disabled={resolvingId === item.id}>
                        {resolvingId === item.id ? 'Resolving…' : 'Resolve'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="paginationRow">
          <button disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>Previous</button>
          <span className="muted">Page {page} of {Math.max(1, Math.ceil(total / perPage))}</span>
          <button disabled={page * perPage >= total} onClick={() => setPage((current) => current + 1)}>Next</button>
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
