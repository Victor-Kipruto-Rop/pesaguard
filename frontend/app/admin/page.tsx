'use client';

import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import {
  LayoutDashboard,
  Search,
  Bell,
  ChevronDown,
  CreditCard,
  RefreshCcw,
  AlertTriangle,
  FileText,
  Box,
  Settings,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  ArrowRight,
} from 'lucide-react';

const sidebarItems = [
  { label: 'Overview', icon: LayoutDashboard, active: true },
  { label: 'Transactions', icon: CreditCard },
  { label: 'Reconciliation', icon: RefreshCcw },
  { label: 'Anomalies', icon: AlertTriangle },
  { label: 'Reports', icon: FileText },
  { label: 'Alerts', icon: Bell },
  { label: 'Integrations', icon: Box },
  { label: 'Settings', icon: Settings },
];

const statCards = [
  {
    label: 'Transactions Processed Today',
    value: 128543,
    unit: '',
    trend: 12.4,
    trendLabel: 'vs yesterday',
    icon: CreditCard,
    accent: 'emerald',
  },
  {
    label: 'Reconciliation Match Rate',
    value: 98.67,
    unit: '%',
    trend: 0.73,
    trendLabel: 'vs yesterday',
    icon: ShieldCheck,
    accent: 'emerald',
  },
  {
    label: 'Open Anomalies',
    value: 7,
    unit: '',
    trendLabel: 'High severity',
    icon: AlertTriangle,
    accent: 'amber',
    extra: '2',
  },
  {
    label: 'System Uptime (24h)',
    value: 99.98,
    unit: '%',
    trend: 0.01,
    trendLabel: 'vs yesterday',
    icon: ShieldCheck,
    accent: 'emerald',
  },
];

const chart7d = [
  { date: 'May 8', value: 98.0 },
  { date: 'May 9', value: 98.7 },
  { date: 'May 10', value: 97.8 },
  { date: 'May 11', value: 98.4 },
  { date: 'May 12', value: 98.92 },
  { date: 'May 13', value: 98.75 },
  { date: 'May 14', value: 99.0 },
];

const chart30d = Array.from({ length: 30 }, (_, index) => ({
  date: `Day ${index + 1}`,
  value: Number((96 + Math.sin(index / 3) * 1.8 + ((index % 6) * 0.1 - 0.3)).toFixed(2)),
}));

const feedItems = [
  { id: '1', time: '10:21:43 AM', description: 'M-Pesa STK Push from 2547***123', amount: 'KES 1,250.00', status: 'Matched' },
  { id: '2', time: '10:21:39 AM', description: 'PayBill 247247 from 2547***456', amount: 'KES 2,500.00', status: 'Matched' },
  { id: '3', time: '10:21:34 AM', description: 'Customer Payment from 2547***789', amount: 'KES 750.00', status: 'Pending' },
  { id: '4', time: '10:21:28 AM', description: 'M-Pesa STK Push from 2547***321', amount: 'KES 5,000.00', status: 'Matched' },
  { id: '5', time: '10:21:22 AM', description: 'PayBill 247247 from 2547***654', amount: 'KES 300.00', status: 'Flagged' },
  { id: '6', time: '10:21:16 AM', description: 'Customer Payment from 2547***987', amount: 'KES 1,150.00', status: 'Matched' },
];

function useCountUp(value: number, duration = 900) {
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    let start: number | null = null;
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      setCurrent(value * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) requestAnimationFrame(step);
    };
    const frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);
  return current;
}

function StatTile({ card, delay }: { card: typeof statCards[number]; delay: number }) {
  const animatedValue = useCountUp(card.value);
  const colorClass = card.accent === 'amber' ? 'accent-amber' : 'accent-emerald';

  return (
    <div className="stat-card" style={{ animationDelay: `${delay}ms` }}>
      <div className="stat-card-top">
        <div className={`stat-icon ${colorClass}`}>
          <card.icon size={18} />
        </div>
        <div>
          <div className="stat-label">{card.label}</div>
          <div className="stat-value">
            {card.unit === '%' ? animatedValue.toFixed(2) : Math.round(animatedValue).toLocaleString()}
            {card.unit}
          </div>
        </div>
      </div>
      <div className="stat-card-bottom">
        <div>{card.trendLabel}</div>
        {card.trend !== undefined ? (
          <div className={`trend-pill ${card.trend >= 0 ? 'trend-up' : 'trend-down'}`}>
            {card.trend >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
            <span>{Math.abs(card.trend)}%</span>
          </div>
        ) : (
          <div className="severity-pill">
            <span className="severity-dot" />
            <span>{card.extra ?? '0'}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function PulseLine() {
  return (
    <div className="header-pulse-container-inner" aria-hidden="true">
      <svg viewBox="0 0 160 24" className="header-pulse-svg" preserveAspectRatio="none">
        <polyline points="0,12 30,12 38,6 46,18 52,12 68,12 76,12 84,6 92,18 100,12 160,12" fill="none" stroke="#2edc87" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function AdminDashboardPage() {
  const [range, setRange] = useState(7);
  const [activeRange, setActiveRange] = useState(7);
  const [viewMode] = useState('Daily');

  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="brand-title">PesaGuard</div>
            <div className="brand-subtitle">Real-Time Reconciliation</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.label} className={`nav-item ${item.active ? 'nav-active' : ''}`} aria-current={item.active ? 'page' : undefined}>
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <div className="status-dot" />
          <div>
            <div className="status-label">All systems connected</div>
            <div className="status-time">Last heartbeat 10:21:43 AM</div>
          </div>
        </div>

        <button className="sidebar-collapse">Collapse</button>
      </aside>

      <div className="admin-main">
        <header className="admin-header">
          <div className="search-bar">
            <Search size={16} />
            <input type="text" placeholder="Search transactions, references, users..." aria-label="Search" />
            <span className="shortcut">⌘K</span>
          </div>
          <div className="header-pulse-container">
            <PulseLine />
          </div>
          <div className="header-actions">
            <div className="live-chip">
              <span />
              Live
            </div>
            <button className="icon-button" aria-label="Notifications">
              <Bell size={18} />
              <span className="badge">3</span>
            </button>
            <div className="profile-pill">
              <span className="profile-avatar">VK</span>
              <div className="profile-info">
                <div className="profile-name">Victor Kipruto</div>
                <div className="profile-role">
                  Admin <ChevronDown size={14} />
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="admin-content">
          <section className="stats-grid">
            {statCards.map((card, index) => (
              <StatTile key={card.label} card={card} delay={index * 80} />
            ))}
          </section>

          <section className="chart-feed-grid">
            <div className="chart-panel">
              <div className="panel-header">
                <div className="panel-title">Match Rate Trend</div>
                <div className="panel-actions">
                  <div className="range-tabs">
                    {[7, 30].map((option) => (
                      <button key={option} className={activeRange === option ? 'range-button active' : 'range-button'} onClick={() => { setActiveRange(option); setRange(option); }}>
                        {option} Days
                      </button>
                    ))}
                  </div>
                  <button className="view-mode">{viewMode} <ChevronDown size={14} /></button>
                </div>
              </div>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={activeRange === 7 ? chart7d : chart30d} margin={{ top: 20, right: 20, left: -16, bottom: 0 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="date" tick={{ fill: '#8FA69C', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[95, 100]} tick={{ fill: '#8FA69C', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: '#0F241D', border: '1px solid rgba(60, 221, 148, 0.18)', borderRadius: 10, color: '#F4FBF8' }}
                      labelStyle={{ color: '#8FA69C' }}
                      itemStyle={{ color: '#2ECC87' }}
                    />
                    <Line type="monotone" dataKey="value" stroke="#2ECC87" strokeWidth={3} dot={{ r: 3, fill: '#2ECC87' }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-footer">
                <span className="legend-dot" />
                <span>Match Rate (%)</span>
              </div>
            </div>

            <div className="feed-panel">
              <div className="panel-header">
                <div className="panel-title">Live Activity Feed</div>
                <div className="panel-live">
                  <span />
                  Live
                </div>
              </div>
              <div className="feed-list">
                {feedItems.map((item) => (
                  <div key={item.id} className="feed-item">
                    <div>
                      <div className="feed-time">{item.time}</div>
                      <div className="feed-description">{item.description}</div>
                    </div>
                          <div className="feed-meta">
                      <div className={`feed-status ${item.status.toLowerCase()}`}>
                        <span className="status-dot-small" />
                        {item.status}
                      </div>
                      <div className="feed-amount">{item.amount}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="action-grid">
            <button className="action-card action-warning">
              <div className="action-card-left">
                <div className="action-icon bg-amber-soft">
                  <AlertTriangle size={18} />
                </div>
                <div>
                  <div className="action-title">Review Anomalies</div>
                  <div className="action-amount">7</div>
                  <div className="action-subtitle"><span className="severity-dot-red" />2 high severity</div>
                  <div className="action-description">Review and resolve anomalies affecting reconciliation accuracy</div>
                </div>
              </div>
              <div className="action-button">
                View Anomalies
                <ArrowRight size={16} />
              </div>
            </button>

            <button className="action-card action-success">
              <div className="action-card-left">
                <div className="action-icon bg-emerald-soft">
                  <RefreshCcw size={18} />
                </div>
                <div>
                  <div className="action-title">Unmatched Transactions</div>
                  <div className="action-amount">1,234</div>
                  <div className="action-subtitle">1.33% of total</div>
                  <div className="action-description">Transactions pending match review and resolution</div>
                </div>
              </div>
              <div className="action-button">
                View Reconciliation
                <ArrowRight size={16} />
              </div>
            </button>
          </section>

          <footer className="dashboard-footer">© 2025 PesaGuard. All rights reserved.</footer>
        </main>
      </div>

      <style jsx global>{`
        :root {
          color-scheme: dark;
        }

        .admin-shell {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 280px 1fr;
          background: #07110f;
          color: #f4fbf8;
          font-family: 'Inter', system-ui, sans-serif;
        }

        .sidebar {
          display: flex;
          flex-direction: column;
          gap: 24px;
          padding: 28px 20px;
          background: linear-gradient(180deg, #081210 0%, #0c1f1a 100%);
          border-right: 1px solid rgba(46, 204, 135, 0.08);
        }

        .sidebar-brand {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px 12px;
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 18px;
          background: rgba(17, 39, 31, 0.72);
        }

        .brand-icon {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: grid;
          place-items: center;
          background: rgba(46, 204, 135, 0.12);
          color: #2edc87;
          border: 1px solid rgba(46, 204, 135, 0.16);
        }

        .brand-title {
          font-size: 1rem;
          font-weight: 700;
        }

        .brand-subtitle {
          font-size: 0.82rem;
          color: #8fa69c;
        }

        .sidebar-nav {
          display: grid;
          gap: 10px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 14px;
          border-radius: 16px;
          background: transparent;
          border: none;
          color: #b6c9bd;
          cursor: pointer;
          transition: background 0.2s ease, color 0.2s ease;
          text-align: left;
          font-size: 0.95rem;
        }

        .nav-item:hover,
        .nav-active {
          color: #f4fbf8;
          background: rgba(46, 204, 135, 0.08);
          box-shadow: 0 10px 30px rgba(11, 39, 32, 0.15);
        }

        .sidebar-status {
          margin-top: auto;
          padding: 16px 14px;
          border-radius: 18px;
          background: rgba(18, 47, 37, 0.82);
          border: 1px solid rgba(255, 255, 255, 0.05);
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #2edc87;
          box-shadow: 0 0 10px rgba(46, 204, 135, 0.35);
          flex-shrink: 0;
        }

        .status-label {
          font-size: 0.92rem;
          font-weight: 600;
        }

        .status-time {
          font-size: 0.8rem;
          color: #8fa69c;
          margin-top: 2px;
        }

        .sidebar-collapse {
          width: 100%;
          border: none;
          border-radius: 14px;
          padding: 12px 14px;
          background: rgba(255,255,255,0.03);
          color: #8fa69c;
          cursor: pointer;
          font-size: 0.92rem;
        }

        .admin-main {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
        }

        .admin-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 24px 32px 12px;
          border-bottom: 1px solid rgba(46, 204, 135, 0.08);
          background: rgba(1, 10, 10, 0.95);
        }

        .search-bar {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          color: #f4fbf8;
          min-width: 520px;
        }

        .search-bar input {
          border: none;
          outline: none;
          background: transparent;
          color: #f4fbf8;
          flex: 1;
          font-size: 0.95rem;
        }

        .shortcut {
          font-size: 0.8rem;
          color: #8fa69c;
          background: rgba(255,255,255,0.04);
          padding: 6px 10px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,0.08);
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .live-chip {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: #8fa69c;
          font-size: 0.9rem;
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(46, 204, 135, 0.08);
        }

        .live-chip span {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #2edc87;
          box-shadow: 0 0 6px rgba(46, 204, 135, 0.45);
        }

        .icon-button {
          position: relative;
          width: 44px;
          height: 44px;
          display: grid;
          place-items: center;
          border-radius: 14px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          background: rgba(255,255,255,0.03);
          color: #f4fbf8;
          cursor: pointer;
        }

        .badge {
          position: absolute;
          top: 8px;
          right: 8px;
          min-width: 18px;
          height: 18px;
          border-radius: 999px;
          background: #ef4444;
          color: white;
          font-size: 0.72rem;
          display: grid;
          place-items: center;
          padding: 0 5px;
        }

        .profile-pill {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          min-width: 230px;
        }

        .profile-avatar {
          width: 36px;
          height: 36px;
          border-radius: 999px;
          background: #2edc87;
          color: #08201a;
          display: grid;
          place-items: center;
          font-weight: 700;
        }

        .profile-info {
          display: grid;
          gap: 2px;
          color: #f4fbf8;
        }

        .profile-name {
          font-weight: 600;
          font-size: 0.95rem;
        }

        .profile-role {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: #8fa69c;
          font-size: 0.82rem;
        }

        .admin-content {
          padding: 28px 32px 32px;
          display: grid;
          gap: 24px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 20px;
        }

        .stat-card {
          padding: 24px;
          border-radius: 24px;
          background: rgba(10, 27, 25, 0.9);
          border: 1px solid rgba(46, 204, 135, 0.08);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          min-height: 156px;
          opacity: 0;
          animation: fadeInUp 0.48s ease forwards;
        }

        .stat-card-top {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .stat-icon {
          width: 42px;
          height: 42px;
          border-radius: 14px;
          display: grid;
          place-items: center;
          background: rgba(46, 204, 135, 0.12);
        }

        .accent-amber {
          background: rgba(245, 158, 11, 0.12);
          color: #fbbf24;
        }

        .accent-emerald {
          background: rgba(34, 197, 94, 0.12);
          color: #34d399;
        }

        .stat-label {
          font-size: 0.8rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #8fa69c;
          margin-bottom: 10px;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          letter-spacing: 0.04em;
        }

        .stat-card-bottom {
          margin-top: 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          color: #8fa69c;
          font-size: 0.9rem;
        }

        .trend-pill,
        .severity-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.06);
          font-size: 0.82rem;
          color: #f4fbf8;
        }

        .trend-up {
          color: #2edc87;
        }

        .trend-down {
          color: #fb7185;
        }

        .severity-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #ef4444;
          box-shadow: 0 0 8px rgba(239, 68, 68, 0.25);
        }

        .chart-feed-grid {
          display: grid;
          grid-template-columns: 1.8fr 1fr;
          gap: 20px;
        }

        .chart-panel,
        .feed-panel,
        .action-card {
          background: rgba(10, 27, 25, 0.92);
          border: 1px solid rgba(46, 204, 135, 0.08);
          border-radius: 24px;
          box-shadow: 0 30px 80px rgba(0, 0, 0, 0.18);
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          padding: 24px;
          border-bottom: 1px solid rgba(255,255,255,0.04);
        }

        .panel-title {
          font-size: 1rem;
          font-weight: 700;
          color: #f4fbf8;
        }

        .panel-actions {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .range-tabs {
          display: flex;
          gap: 8px;
        }

        .range-button,
        .view-mode {
          border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.04);
          color: #8fa69c;
          padding: 10px 14px;
          border-radius: 14px;
          cursor: pointer;
          font-size: 0.82rem;
        }

        .range-button.active {
          color: #2edc87;
          background: rgba(46, 204, 135, 0.12);
          border-color: rgba(46, 204, 135, 0.16);
        }

        .chart-wrapper {
          padding: 18px 24px 24px;
          min-height: 360px;
        }

        .chart-footer {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 0 24px 24px;
          color: #8fa69c;
          font-size: 0.9rem;
        }

        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #2edc87;
          box-shadow: 0 0 10px rgba(46, 204, 135, 0.45);
        }

        .feed-panel {
          display: flex;
          flex-direction: column;
          min-height: 548px;
        }

        .panel-live {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(46, 204, 135, 0.1);
          color: #8fa69c;
          font-size: 0.85rem;
        }

        .feed-list {
          display: grid;
          gap: 10px;
          padding: 20px 24px 24px;
        }

        .feed-item {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 16px;
          padding: 16px 18px;
          border-radius: 18px;
          border: 1px solid rgba(255,255,255,0.05);
          background: rgba(15, 36, 30, 0.9);
          align-items: center;
        }

        .feed-time {
          font-size: 0.82rem;
          color: #8fa69c;
          margin-bottom: 6px;
        }

        .feed-description {
          color: #f4fbf8;
          font-size: 0.94rem;
          line-height: 1.4;
        }

        .feed-meta {
          display: grid;
          gap: 6px;
          text-align: right;
        }

        .feed-amount {
          font-weight: 700;
          color: #f4fbf8;
        }

        .feed-status {
          font-size: 0.82rem;
          font-weight: 600;
          color: #8fa69c;
        }

        .feed-status.matched {
          color: #2edc87;
        }

        .feed-status.pending {
          color: #f59e0b;
        }

        .feed-status.flagged {
          color: #ef4444;
        }

        .action-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 20px;
        }

        .action-card {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 24px;
          padding: 24px;
          min-height: 160px;
          border-radius: 24px;
          background: rgba(10, 27, 25, 0.92);
          border: 1px solid rgba(255,255,255,0.06);
        }

        .action-card-left {
          display: flex;
          align-items: flex-start;
          gap: 18px;
        }

        .action-icon {
          width: 52px;
          height: 52px;
          border-radius: 18px;
          display: grid;
          place-items: center;
          color: #f4fbf8;
        }

        .bg-amber-soft {
          background: rgba(245, 158, 11, 0.16);
          color: #fbbf24;
        }

        .bg-emerald-soft {
          background: rgba(34, 197, 94, 0.16);
          color: #34d399;
        }

        .action-title {
          font-size: 0.95rem;
          font-weight: 700;
          color: #f4fbf8;
          margin-bottom: 8px;
        }

        .action-amount {
          font-size: 1.9rem;
          font-weight: 700;
          color: #f4fbf8;
          margin-bottom: 8px;
        }

        .action-subtitle {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 0.9rem;
          color: #8fa69c;
          margin-bottom: 10px;
        }

        .severity-dot-red {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #ef4444;
          box-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
        }

        .action-description {
          color: #8fa69c;
          font-size: 0.88rem;
          line-height: 1.5;
          max-width: 320px;
        }

        .action-button {
          align-self: stretch;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 170px;
          border-radius: 16px;
          padding: 12px 18px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
          color: #f4fbf8;
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .action-button:hover {
          background: rgba(255,255,255,0.08);
        }

        .dashboard-footer {
          margin-top: 12px;
          padding: 18px 0 6px;
          text-align: center;
          color: #667d6f;
          font-size: 0.85rem;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(16px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 1280px) {
          .admin-shell {
            grid-template-columns: 1fr;
          }

          .sidebar {
            flex-direction: row;
            gap: 16px;
            align-items: center;
            padding: 18px 16px;
            overflow-x: auto;
          }

          .sidebar-nav {
            grid-auto-flow: column;
            grid-auto-columns: minmax(140px, auto);
            display: grid;
          }

          .sidebar-status,
          .sidebar-collapse {
            display: none;
          }

          .admin-header,
          .admin-content {
            padding-left: 20px;
            padding-right: 20px;
          }

          .stats-grid,
          .chart-feed-grid,
          .action-grid {
            gap: 16px;
          }
        }

        @media (max-width: 860px) {
          .stats-grid,
          .chart-feed-grid,
          .action-grid {
            grid-template-columns: 1fr;
          }

          .search-bar {
            min-width: auto;
            width: 100%;
          }

          .panel-header {
            flex-direction: column;
            align-items: stretch;
          }

          .panel-actions {
            justify-content: space-between;
            width: 100%;
          }

          .feed-panel {
            min-height: auto;
          }
        }
      `}</style>
    </div>
  );
}
