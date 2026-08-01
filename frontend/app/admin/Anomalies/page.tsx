'use client';

import React, { useEffect, useRef, useState } from 'react';
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from 'recharts';
import {
  Search,
  Bell,
  ChevronDown,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

const trendData7 = [
  { d: 'Mon', v: 96.2 },
  { d: 'Tue', v: 97.1 },
  { d: 'Wed', v: 95.8 },
  { d: 'Thu', v: 98.4 },
  { d: 'Fri', v: 97.9 },
  { d: 'Sat', v: 99.1 },
  { d: 'Sun', v: 98.7 },
];

const trendData30 = Array.from({ length: 30 }, (_, i) => ({
  d: `${i + 1}`,
  v: 94 + Math.sin(i / 3) * 2 + Math.random() * 1.5,
}));

const initialFeed = [
  { id: 'SGX9K2L1', amount: 4200, status: 'matched', time: '2m ago' },
  { id: 'PLM7Y3Q8', amount: 18500, status: 'matched', time: '4m ago' },
  { id: 'TRX2A9F4', amount: 950, status: 'pending', time: '6m ago' },
  { id: 'QWE1Z5X2', amount: 32000, status: 'matched', time: '9m ago' },
  { id: 'NBV6C8D3', amount: 1200, status: 'flagged', time: '12m ago' },
];

const statusStyles = {
  matched: { bg: 'bg-emerald-400/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  pending: { bg: 'bg-amber-400/10', text: 'text-amber-400', dot: 'bg-amber-400' },
  flagged: { bg: 'bg-rose-500/10', text: 'text-rose-400', dot: 'bg-rose-400' },
};

function useCountUp(target: number, duration = 700) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start: number | null = null;
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setVal(target * eased);
      if (progress < 1) requestAnimationFrame(step);
    };
    const raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

function StatCard({ label, value, format, trend, icon: Icon, delay }: { label: string; value: number; format: (value: number) => string; trend?: number; icon: React.ElementType; delay: number }) {
  const animated = useCountUp(value);
  return (
    <div
      className="statCard"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="statCardHeader">
        <span className="statCardLabel">{label}</span>
        <Icon size={16} className="statCardIcon" />
      </div>
      <div className="statCardBody">
        <span className="statCardValue">{format(animated)}</span>
        {trend !== undefined && (
          <span className={`statCardTrend ${trend >= 0 ? 'positive' : 'negative'}`}>
            {trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
    </div>
  );
}

function PulseLine() {
  return (
    <div className="pulseLineWrap">
      <svg viewBox="0 0 100 24" className="pulseLineSvg">
        <polyline
          points="0,12 20,12 26,4 32,20 38,12 100,12"
          fill="none"
          stroke="#2ECC87"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="pulseLineAnim"
          style={{ filter: 'drop-shadow(0 0 3px rgba(46,204,135,0.6))' }}
        />
      </svg>
    </div>
  );
}

export default function AdminAnomaliesPage() {
  const [range, setRange] = useState(7);
  const [feed, setFeed] = useState(initialFeed);
  const [flashId, setFlashId] = useState<string | null>(null);
  const idCounter = useRef(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      idCounter.current += 1;
      const statuses = ['matched', 'matched', 'matched', 'pending', 'flagged'] as const;
      const newTx = {
        id: `NEW${idCounter.current}${Math.random().toString(36).slice(2, 5).toUpperCase()}`,
        amount: Math.floor(Math.random() * 40000) + 500,
        status: statuses[Math.floor(Math.random() * statuses.length)],
        time: 'just now',
      };
      setFeed((prev) => [newTx, ...prev.slice(0, 7)]);
      setFlashId(newTx.id);
      window.setTimeout(() => setFlashId(null), 1500);
    }, 5000);
    return () => window.clearInterval(interval);
  }, []);

  const data = range === 7 ? trendData7 : trendData30;
  const anomalyCount = feed.filter((item) => item.status === 'flagged').length;
  const unmatchedCount = feed.filter((item) => item.status === 'pending').length;

  return (
    <main className="adminAnomaliesPage">
      <style jsx global>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseFlow {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        @keyframes rowIn {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .tabular-nums { font-variant-numeric: tabular-nums; }
        .adminAnomaliesPage {
          min-height: 100vh;
          background: linear-gradient(180deg, #0A1F2E 0%, #0B2E24 100%);
          color: #F4FBF8;
          font-family: 'DM Sans', 'Segoe UI', sans-serif;
        }
        .adminAnomaliesPage .topBar {
          position: sticky;
          top: 0;
          z-index: 10;
          backdrop-filter: blur(12px);
          background: rgba(10, 31, 46, 0.72);
          border-bottom: 1px solid rgba(46, 204, 135, 0.2);
          padding: 12px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .adminAnomaliesPage .brandArea {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .adminAnomaliesPage .brandIcon {
          width: 32px;
          height: 32px;
          border-radius: 10px;
          background: linear-gradient(180deg, #124A3B 0%, #0B2E24 100%);
          border: 1px solid rgba(46, 204, 135, 0.35);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .adminAnomaliesPage .brandText {
          font-size: 0.95rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        .adminAnomaliesPage .topActions {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .adminAnomaliesPage .searchBox {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 10px;
          background: #0F241D;
          border: 1px solid rgba(46, 204, 135, 0.24);
          color: #8FA69C;
          font-size: 0.9rem;
        }
        .adminAnomaliesPage .content {
          padding: 24px;
          max-width: 1280px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .adminAnomaliesPage .statGrid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 16px;
        }
        .adminAnomaliesPage .statCard {
          opacity: 0;
          animation: fadeSlideIn 0.5s ease-out forwards;
          border-radius: 16px;
          border: 1px solid rgba(46, 204, 135, 0.24);
          background: #0F241D;
          padding: 20px;
        }
        .adminAnomaliesPage .statCardHeader {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .adminAnomaliesPage .statCardLabel {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: #8FA69C;
        }
        .adminAnomaliesPage .statCardIcon {
          color: rgba(46, 204, 135, 0.72);
        }
        .adminAnomaliesPage .statCardBody {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 12px;
        }
        .adminAnomaliesPage .statCardValue {
          font-family: ui-monospace, SFMono-Regular, monospace;
          font-size: 1.9rem;
          font-weight: 600;
          color: #F4FBF8;
        }
        .adminAnomaliesPage .statCardTrend {
          display: flex;
          align-items: center;
          font-size: 0.8rem;
          font-weight: 600;
        }
        .adminAnomaliesPage .statCardTrend.positive { color: #34d399; }
        .adminAnomaliesPage .statCardTrend.negative { color: #fb7185; }
        .adminAnomaliesPage .chartFeedGrid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 16px;
        }
        .adminAnomaliesPage .panel {
          border-radius: 16px;
          border: 1px solid rgba(46, 204, 135, 0.24);
          background: #0F241D;
          padding: 20px;
        }
        .adminAnomaliesPage .panelHeader {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 14px;
        }
        .adminAnomaliesPage .panelTitle {
          font-size: 0.95rem;
          font-weight: 600;
        }
        .adminAnomaliesPage .rangeButtons {
          display: flex;
          gap: 6px;
          font-size: 0.8rem;
        }
        .adminAnomaliesPage .rangeButton {
          border: none;
          background: transparent;
          color: #8FA69C;
          padding: 6px 10px;
          border-radius: 8px;
          cursor: pointer;
        }
        .adminAnomaliesPage .rangeButton.active {
          background: rgba(46, 204, 135, 0.16);
          color: #2ECC87;
        }
        .adminAnomaliesPage .feedList {
          display: flex;
          flex-direction: column;
          gap: 8px;
          overflow: hidden;
          flex: 1;
        }
        .adminAnomaliesPage .feedRow {
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid rgba(46, 204, 135, 0.12);
          padding: 8px 0;
          font-size: 0.85rem;
          animation: rowIn 0.4s ease-out;
        }
        .adminAnomaliesPage .feedRow:last-child { border-bottom: 0; }
        .adminAnomaliesPage .feedLeft {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .adminAnomaliesPage .feedDot { width: 8px; height: 8px; border-radius: 999px; }
        .adminAnomaliesPage .feedId { font-family: ui-monospace, SFMono-Regular, monospace; color: #8FA69C; font-size: 0.75rem; }
        .adminAnomaliesPage .feedAmount { font-family: ui-monospace, SFMono-Regular, monospace; font-size: 0.8rem; }
        .adminAnomaliesPage .feedTime { color: #8FA69C; width: 58px; text-align: right; }
        .adminAnomaliesPage .quickCards {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 16px;
        }
        .adminAnomaliesPage .quickCard {
          display: flex;
          align-items: center;
          justify-content: space-between;
          text-align: left;
          width: 100%;
          border-radius: 16px;
          border: 1px solid rgba(46, 204, 135, 0.24);
          background: #0F241D;
          padding: 18px;
          color: #F4FBF8;
          cursor: pointer;
        }
        .adminAnomaliesPage .quickCardText { display: flex; flex-direction: column; gap: 4px; }
        .adminAnomaliesPage .quickCardHint { font-size: 0.8rem; color: #8FA69C; }
        .adminAnomaliesPage .pulseLineWrap {
          position: relative;
          height: 24px;
          width: 96px;
          overflow: hidden;
        }
        .adminAnomaliesPage .pulseLineSvg {
          width: 100%;
          height: 100%;
        }
        .adminAnomaliesPage .pulseLineAnim {
          animation: pulseFlow 2s ease-in-out infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .adminAnomaliesPage * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; }
        }
        @media (max-width: 960px) {
          .adminAnomaliesPage .statGrid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .adminAnomaliesPage .chartFeedGrid { grid-template-columns: 1fr; }
          .adminAnomaliesPage .quickCards { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .adminAnomaliesPage .content { padding: 16px; }
          .adminAnomaliesPage .topBar { padding: 12px 16px; }
          .adminAnomaliesPage .topActions { gap: 10px; }
          .adminAnomaliesPage .searchBox span:last-child { display: none; }
          .adminAnomaliesPage .statGrid { grid-template-columns: 1fr; }
        }
      `}</style>

      <div className="topBar">
        <div className="brandArea">
          <div className="brandIcon">
            <ShieldCheck size={16} className="statCardIcon" />
          </div>
          <span className="brandText">PesaGuard</span>
          <PulseLine />
        </div>
        <div className="topActions">
          <div className="searchBox">
            <Search size={14} />
            <span>Search transactions…</span>
          </div>
          <Bell size={16} className="statCardIcon" />
          <div className="brandIcon" style={{ width: 28, height: 28, borderRadius: 999 }} />
        </div>
      </div>

      <div className="content">
        <div className="statGrid">
          <StatCard label="Transactions Today" value={1284} format={(value) => Math.round(value).toLocaleString()} trend={4.2} icon={Activity} delay={0} />
          <StatCard label="Match Rate" value={98.7} format={(value) => `${value.toFixed(1)}%`} trend={0.6} icon={CheckCircle2} delay={70} />
          <StatCard label="Open Anomalies" value={anomalyCount} format={(value) => Math.round(value).toString()} icon={AlertTriangle} delay={140} />
          <StatCard label="Uptime (24h)" value={99.98} format={(value) => `${value.toFixed(2)}%`} icon={Clock} delay={210} />
        </div>

        <div className="chartFeedGrid">
          <div className="panel">
            <div className="panelHeader">
              <span className="panelTitle">Reconciliation Match Rate</span>
              <div className="rangeButtons">
                {[7, 30].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setRange(item)}
                    className={`rangeButton ${range === item ? 'active' : ''}`}
                  >
                    {item}d
                  </button>
                ))}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data}>
                <YAxis hide domain={['dataMin - 2', 'dataMax + 2']} />
                <Tooltip
                  contentStyle={{ background: '#0A1F2E', border: '1px solid #1A3A2E', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#8FA69C' }}
                  itemStyle={{ color: '#2ECC87' }}
                />
                <Line type="monotone" dataKey="v" stroke="#2ECC87" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="panelHeader">
              <span className="panelTitle">Live Activity</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span className="feedDot" style={{ background: '#34d399' }} />
                <span style={{ color: '#8FA69C', fontSize: '0.8rem' }}>Live</span>
              </div>
            </div>
            <div className="feedList">
              {feed.map((item) => {
                const style = statusStyles[item.status as keyof typeof statusStyles];
                return (
                  <div
                    key={item.id}
                    className="feedRow"
                    style={{ backgroundColor: flashId === item.id ? 'rgba(46,204,135,0.08)' : 'transparent' }}
                  >
                    <div className="feedLeft">
                      <span className={`feedDot ${style.dot}`} />
                      <span className="feedId">{item.id}</span>
                    </div>
                    <span className="feedAmount">KES {item.amount.toLocaleString()}</span>
                    <span className="feedTime">{item.time}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="quickCards">
          <button type="button" className="quickCard">
            <div className="quickCardText">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} className="statCardIcon" />
                <span className="panelTitle">Review Anomalies</span>
              </div>
              <span className="quickCardHint">
                {anomalyCount > 0 ? `${anomalyCount} flagged transaction${anomalyCount > 1 ? 's' : ''} need review` : 'No anomalies right now'}
              </span>
            </div>
            <ChevronDown size={16} className="statCardIcon" style={{ transform: 'rotate(-90deg)' }} />
          </button>

          <button type="button" className="quickCard">
            <div className="quickCardText">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={16} className="statCardIcon" />
                <span className="panelTitle">Unmatched Transactions</span>
              </div>
              <span className="quickCardHint">
                {unmatchedCount > 0 ? `${unmatchedCount} pending reconciliation` : 'Everything is reconciled'}
              </span>
            </div>
            <ChevronDown size={16} className="statCardIcon" style={{ transform: 'rotate(-90deg)' }} />
          </button>
        </div>
      </div>
    </main>
  );
}
