'use client';

import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export interface TrendDataPoint {
  day: string;
  value: number;
  resolved?: number;
}

interface TrendChartProps {
  data: TrendDataPoint[];
  title: string;
  height?: number;
}

export function TrendLineChart({ data, title, height = 280 }: TrendChartProps) {
  return (
    <div className="chartContainer">
      <div className="chartTitle">{title}</div>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="var(--accent)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="day" stroke="var(--muted)" />
          <YAxis stroke="var(--muted)" />
          <Tooltip
            contentStyle={{
              background: 'rgba(16,27,47,0.95)',
              border: '1px solid rgba(68,215,182,0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
          />
          <Area type="monotone" dataKey="value" stroke="var(--accent)" fillOpacity={1} fill="url(#colorValue)" isAnimationActive={true} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ResolutionBarChart({ data, height = 280 }: { data: TrendDataPoint[], height?: number }) {
  return (
    <div className="chartContainer">
      <div className="chartTitle">Resolution vs. Open</div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="day" stroke="var(--muted)" />
          <YAxis stroke="var(--muted)" />
          <Tooltip
            contentStyle={{
              background: 'rgba(16,27,47,0.95)',
              border: '1px solid rgba(68,215,182,0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
          />
          <Bar dataKey="value" fill="var(--accent)" isAnimationActive={true} />
          <Bar dataKey="resolved" fill="rgba(68,215,182,0.4)" isAnimationActive={true} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
