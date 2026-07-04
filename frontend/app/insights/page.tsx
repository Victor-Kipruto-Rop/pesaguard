'use client';

import { useEffect, useMemo, useState } from 'react';
import { TrendLineChart, ResolutionBarChart } from '../../components/Charts';

interface MetricsData {
  trend_series: number[];
  severity_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  open_count: number;
  resolved_count: number;
  transactions_per_minute: number;
  reconciliation_latency_p50: number;
  reconciliation_latency_p95: number;
  discrepancy_rate: number;
}

interface SLAMetrics {
  on_track: number;
  warning: number;
  breaching: number;
  total: number;
}

interface ResolutionMetrics {
  average_resolution_time: number;
  median_resolution_time: number;
  p95_resolution_time: number;
}

interface OperatorStats {
  operator: string;
  assigned_count: number;
  resolved_count: number;
  average_resolution_time: number;
}

export default function InsightsPage() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [slaMetrics, setSLAMetrics] = useState<SLAMetrics | null>(null);
  const [resolutionMetrics, setResolutionMetrics] = useState<ResolutionMetrics | null>(null);
  const [operatorStats, setOperatorStats] = useState<OperatorStats[]>([]);
  const [loading, setLoading] = useState(true);

  const chartData = useMemo(() => {
    if (!metrics) return [];
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return (metrics.trend_series || []).map((value, index) => ({
      day: days[index] || `D${index + 1}`,
      value,
      resolved: Math.floor(value * 0.6),
    }));
  }, [metrics]);

  const severityChartData = useMemo(() => {
    if (!metrics) return [];
    return Object.entries(metrics.severity_breakdown || {}).map(([name, count]) => ({
      day: name.charAt(0).toUpperCase() + name.slice(1),
      value: count as number,
      resolved: Math.floor((count as number) * 0.5),
    }));
  }, [metrics]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [metricsRes, slaRes, resolutionRes, operatorRes] = await Promise.all([
          fetch('http://127.0.0.1:5001/metrics'),
          fetch('http://127.0.0.1:5001/analytics/sla-metrics'),
          fetch('http://127.0.0.1:5001/analytics/resolution-times'),
          fetch('http://127.0.0.1:5001/analytics/operator-stats'),
        ]);

        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (slaRes.ok) setSLAMetrics(await slaRes.json());
        if (resolutionRes.ok) setResolutionMetrics(await resolutionRes.json());
        if (operatorRes.ok) setOperatorStats(await operatorRes.json());
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="shell">
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">Analytics & Insights</p>
          <h1>Operational metrics and performance</h1>
          <p className="muted">Track system health, SLA compliance, resolution efficiency, and operator performance.</p>
        </div>
      </section>

      {loading && !metrics ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted-color)' }}>
          Loading analytics...
        </div>
      ) : (
        <>
          <section className="grid splitGrid">
            <article className="card">
              <TrendLineChart data={chartData} title="Exception trend (7 days)" height={260} />
            </article>
            <article className="card">
              <TrendLineChart data={severityChartData} title="Incidents by severity" height={260} />
            </article>
          </section>

          <section className="grid splitGrid">
            <article className="card">
              <div className="sectionTitle">SLA compliance</div>
              {slaMetrics ? (
                <div style={{ display: 'grid', gap: 16, marginTop: 20 }}>
                  <div className="metricRow">
                    <span className="muted">On track</span>
                    <strong className="ok">{slaMetrics.on_track}</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Warning zone</span>
                    <strong className="warning">{slaMetrics.warning}</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Breaching</span>
                    <strong className="danger">{slaMetrics.breaching}</strong>
                  </div>
                  <div className="metricRow" style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
                    <span className="muted">Total SLA incidents</span>
                    <strong>{slaMetrics.total}</strong>
                  </div>
                </div>
              ) : (
                <div className="muted">No SLA data available</div>
              )}
            </article>
            <article className="card">
              <div className="sectionTitle">Resolution metrics</div>
              {resolutionMetrics ? (
                <div style={{ display: 'grid', gap: 16, marginTop: 20 }}>
                  <div className="metricRow">
                    <span className="muted">Average time</span>
                    <strong>{resolutionMetrics.average_resolution_time}m</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Median time</span>
                    <strong>{resolutionMetrics.median_resolution_time}m</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">P95 time</span>
                    <strong>{resolutionMetrics.p95_resolution_time}m</strong>
                  </div>
                  <div className="metricRow" style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
                    <span className="muted">Target (critical)</span>
                    <strong>30m</strong>
                  </div>
                </div>
              ) : (
                <div className="muted">No resolution data available</div>
              )}
            </article>
          </section>

          <section className="card">
            <div className="sectionTitle">Operator performance</div>
            {operatorStats.length > 0 ? (
              <div style={{ marginTop: 20, overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th style={{ textAlign: 'left', padding: '12px 0', color: 'var(--muted-color)', fontWeight: 500 }}>Operator</th>
                      <th style={{ textAlign: 'right', padding: '12px 0', color: 'var(--muted-color)', fontWeight: 500 }}>Assigned</th>
                      <th style={{ textAlign: 'right', padding: '12px 0', color: 'var(--muted-color)', fontWeight: 500 }}>Resolved</th>
                      <th style={{ textAlign: 'right', padding: '12px 0', color: 'var(--muted-color)', fontWeight: 500 }}>Avg time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {operatorStats.map((stat) => (
                      <tr key={stat.operator} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '12px 0' }}>{stat.operator}</td>
                        <td style={{ textAlign: 'right', padding: '12px 0' }}>{stat.assigned_count}</td>
                        <td style={{ textAlign: 'right', padding: '12px 0' }}>{stat.resolved_count}</td>
                        <td style={{ textAlign: 'right', padding: '12px 0' }}>{stat.average_resolution_time}m</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="muted" style={{ marginTop: 20 }}>No operator statistics available yet</div>
            )}
          </section>

          <section className="grid splitGrid">
            <article className="card">
              <div className="sectionTitle">System vitals</div>
              {metrics && (
                <div style={{ display: 'grid', gap: 16, marginTop: 20 }}>
                  <div className="metricRow">
                    <span className="muted">Transactions/min</span>
                    <strong>{metrics.transactions_per_minute}</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Latency P50</span>
                    <strong>{metrics.reconciliation_latency_p50}ms</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Latency P95</span>
                    <strong>{metrics.reconciliation_latency_p95}ms</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Discrepancy rate</span>
                    <strong>{(metrics.discrepancy_rate * 100).toFixed(2)}%</strong>
                  </div>
                </div>
              )}
            </article>
            <article className="card">
              <div className="sectionTitle">Open vs Resolved</div>
              {metrics && (
                <div style={{ display: 'grid', gap: 16, marginTop: 20 }}>
                  <div className="metricRow">
                    <span className="muted">Open incidents</span>
                    <strong className="warning">{metrics.open_count}</strong>
                  </div>
                  <div className="metricRow">
                    <span className="muted">Resolved incidents</span>
                    <strong className="ok">{metrics.resolved_count}</strong>
                  </div>
                  <div className="metricRow" style={{ borderTop: '1px solid var(--border)', paddingTop: 12, marginTop: 12 }}>
                    <span className="muted">Total incidents</span>
                    <strong>{metrics.open_count + metrics.resolved_count}</strong>
                  </div>
                </div>
              )}
            </article>
          </section>
        </>
      )}
    </main>
  );
}
