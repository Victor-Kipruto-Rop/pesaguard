'use client';

import { useState, useEffect } from 'react';

interface ReconciliationReport {
  report_period_days: number;
  generated_at: string;
  summary: {
    total_incidents: number;
    resolved: number;
    open: number;
    resolution_rate: number;
    average_resolution_minutes: number;
  };
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  critical_count: number;
  sla_compliant_percentage: number;
}

interface TrendData {
  weekly: Array<{ week: string; incidents: number; resolved: number; open: number }>;
  monthly: Array<{ month: string; incidents: number; resolved: number; open: number }>;
}

export default function ToolsPage() {
  const [report, setReport] = useState<ReconciliationReport | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [reportDays, setReportDays] = useState('7');
  const [escalationMinutes, setEscalationMinutes] = useState('45');
  const [bulkAssignee, setBulkAssignee] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [feedback, setFeedback] = useState('');

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5001/incidents/filters/presets');
      if (res.ok) {
        const data = await res.json();
        setPresets(data.presets);
      }
    } catch (error) {
      console.error('Failed to load presets:', error);
    }
  };

  const generateReport = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:5001/analytics/reconciliation-report?days=${reportDays}`);
      if (res.ok) {
        const data = await res.json();
        setReport(data);
        showFeedback('Report generated successfully');
      }
    } catch (error) {
      showFeedback('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const loadTrends = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5001/analytics/incident-trends');
      if (res.ok) {
        const data = await res.json();
        setTrends(data);
        showFeedback('Trends loaded');
      }
    } catch (error) {
      showFeedback('Failed to load trends');
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5001/discrepancies/export/csv');
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pesaguard_incidents_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        showFeedback('CSV exported successfully');
      }
    } catch (error) {
      showFeedback('Failed to export CSV');
    }
  };

  const autoEscalate = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:5001/incidents/auto-escalate?escalation_minutes=${escalationMinutes}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        showFeedback(`✓ Auto-escalated ${data.count} critical incidents`);
      }
    } catch (error) {
      showFeedback('Failed to auto-escalate');
    }
  };

  const bulkAssign = async () => {
    if (!bulkAssignee.trim()) {
      showFeedback('Please enter an assignee');
      return;
    }
    try {
      const res = await fetch('http://127.0.0.1:5001/incidents/bulk-assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ids: selectedIds.length > 0 ? selectedIds : [],
          assignee: bulkAssignee,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        showFeedback(`✓ Assigned ${data.updated} incidents to ${bulkAssignee}`);
        setBulkAssignee('');
      }
    } catch (error) {
      showFeedback('Failed to bulk assign');
    }
  };

  const showFeedback = (msg: string) => {
    setFeedback(msg);
    setTimeout(() => setFeedback(''), 3000);
  };

  return (
    <main className="shell">
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">Advanced Tools</p>
          <h1>Bulk operations & reporting</h1>
          <p className="muted">CSV exports, trend analysis, auto-escalation, and reconciliation reports.</p>
        </div>
      </section>

      {feedback && (
        <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid #10b981', color: '#10b981', marginBottom: 20, fontSize: '14px' }}>
          {feedback}
        </div>
      )}

      <section className="grid splitGrid">
        <article className="card">
          <div className="sectionTitle">🔄 Auto-escalation</div>
          <div style={{ marginTop: 16 }}>
            <label style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>
              Escalate after (minutes)
            </label>
            <input
              type="number"
              value={escalationMinutes}
              onChange={(e) => setEscalationMinutes(e.target.value)}
              min="10"
              max="120"
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--input-bg)',
                color: 'white',
                fontSize: '14px',
              }}
            />
            <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 8 }}>
              Automatically escalate unresolved critical incidents to On-Call Lead
            </p>
            <button
              onClick={autoEscalate}
              style={{
                marginTop: 12,
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(249, 115, 22, 0.2)',
                border: '1px solid #f97316',
                color: '#fb923c',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Escalate Now
            </button>
          </div>
        </article>

        <article className="card">
          <div className="sectionTitle">📥 Export & Download</div>
          <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
            <p style={{ fontSize: '13px', color: 'var(--muted-color)' }}>Export all incidents as CSV file</p>
            <button
              onClick={exportCSV}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid #3b82f6',
                color: '#60a5fa',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              ⬇️ Download CSV
            </button>
          </div>
        </article>
      </section>

      <section className="grid splitGrid">
        <article className="card">
          <div className="sectionTitle">📋 Reconciliation Report</div>
          <div style={{ marginTop: 16 }}>
            <label style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>
              Report period (days)
            </label>
            <input
              type="number"
              value={reportDays}
              onChange={(e) => setReportDays(e.target.value)}
              min="1"
              max="90"
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--input-bg)',
                color: 'white',
                fontSize: '14px',
              }}
            />
            <button
              onClick={generateReport}
              disabled={loading}
              style={{
                marginTop: 12,
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%)',
                border: 'none',
                color: 'white',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? '⏳ Generating...' : '📊 Generate Report'}
            </button>
          </div>
        </article>

        <article className="card">
          <div className="sectionTitle">👥 Bulk Assign</div>
          <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
            <input
              type="text"
              value={bulkAssignee}
              onChange={(e) => setBulkAssignee(e.target.value)}
              placeholder="Operator name"
              style={{
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--input-bg)',
                color: 'white',
                fontSize: '13px',
              }}
            />
            <button
              onClick={bulkAssign}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(139, 92, 246, 0.2)',
                border: '1px solid #a78bfa',
                color: '#c4b5fd',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              🔗 Assign
            </button>
          </div>
        </article>
      </section>

      {report && (
        <section className="card">
          <div className="sectionTitle">📊 Report Results</div>
          <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            <div style={{ padding: 12, background: 'rgba(16, 185, 129, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>Total Incidents</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'white', marginTop: 4 }}>{report.summary.total_incidents}</div>
            </div>
            <div style={{ padding: 12, background: 'rgba(34, 197, 94, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>Resolved</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#10b981', marginTop: 4 }}>{report.summary.resolved}</div>
            </div>
            <div style={{ padding: 12, background: 'rgba(249, 115, 22, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>Open</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#f97316', marginTop: 4 }}>{report.summary.open}</div>
            </div>
            <div style={{ padding: 12, background: 'rgba(59, 130, 246, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>Resolution Rate</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#3b82f6', marginTop: 4 }}>{(report.summary.resolution_rate * 100).toFixed(1)}%</div>
            </div>
            <div style={{ padding: 12, background: 'rgba(59, 130, 246, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>SLA Compliance</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#3b82f6', marginTop: 4 }}>{report.sla_compliant_percentage}%</div>
            </div>
            <div style={{ padding: 12, background: 'rgba(239, 68, 68, 0.05)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted-color)' }}>Critical</div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: '#ef4444', marginTop: 4 }}>{report.critical_count}</div>
            </div>
          </div>

          <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 8, color: 'white' }}>By Severity</h4>
              {Object.entries(report.by_severity).map(([sev, count]) => (
                <div key={sev} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted-color)', marginBottom: 4 }}>
                  <span>{sev}</span>
                  <strong style={{ color: 'white' }}>{count}</strong>
                </div>
              ))}
            </div>
            <div>
              <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 8, color: 'white' }}>By Status</h4>
              {Object.entries(report.by_status).map(([stat, count]) => (
                <div key={stat} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted-color)', marginBottom: 4 }}>
                  <span>{stat}</span>
                  <strong style={{ color: 'white' }}>{count}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {trends && (
        <section className="card">
          <div className="sectionTitle">📈 Incident Trends</div>
          <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 12, color: 'white' }}>Last 4 Weeks</h4>
              <div style={{ display: 'grid', gap: 8 }}>
                {trends.weekly.map((week) => (
                  <div key={week.week} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted-color)' }}>
                    <span>{week.week}</span>
                    <div style={{ display: 'flex', gap: 12 }}>
                      <span style={{ color: '#ef4444' }}>🔴 {week.open}</span>
                      <span style={{ color: '#10b981' }}>🟢 {week.resolved}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 12, color: 'white' }}>Last 12 Months</h4>
              <div style={{ display: 'grid', gap: 8 }}>
                {trends.monthly.slice(0, 6).map((month) => (
                  <div key={month.month} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted-color)' }}>
                    <span>{month.month}</span>
                    <div style={{ display: 'flex', gap: 12 }}>
                      <span style={{ color: '#ef4444' }}>🔴 {month.open}</span>
                      <span style={{ color: '#10b981' }}>🟢 {month.resolved}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <button
            onClick={loadTrends}
            style={{
              marginTop: 16,
              width: '100%',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid var(--border)',
              color: 'var(--text)',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Refresh Trends
          </button>
        </section>
      )}

      {!trends && !report && (
        <section className="card" style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted-color)' }}>
          <p>👇 Select a tool above to get started</p>
        </section>
      )}
    </main>
  );
}
