'use client';

import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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
              <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.45} />
              <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="day" stroke="var(--muted)" tickLine={false} axisLine={false} />
          <YAxis stroke="var(--muted)" tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              background: 'rgba(16, 27, 47, 0.95)',
              border: '1px solid rgba(68, 215, 182, 0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
            itemStyle={{ color: 'var(--text)' }}
          />
          <Area type="monotone" dataKey="value" stroke="var(--accent)" fill="url(#colorValue)" isAnimationActive={true} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ResolutionBarChart({ data, height = 280 }: { data: TrendDataPoint[]; height?: number }) {
  return (
    <div className="chartContainer">
      <div className="chartTitle">Resolution vs. Open</div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
          <XAxis dataKey="day" stroke="var(--muted)" tickLine={false} axisLine={false} />
          <YAxis stroke="var(--muted)" tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              background: 'rgba(16, 27, 47, 0.95)',
              border: '1px solid rgba(68, 215, 182, 0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
            itemStyle={{ color: 'var(--text)' }}
          />
          <Bar dataKey="value" fill="var(--accent)" isAnimationActive={true} />
          <Bar dataKey="resolved" fill="rgba(68,215,182,0.4)" isAnimationActive={true} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SeverityDonutChart({ data, title, height = 280 }: { data: Array<{ name: string; value: number }>; title: string; height?: number }) {
  const colors: Record<string, string> = {
    Critical: 'var(--danger)',
    High: 'var(--warning)',
    Medium: '#F7B844',
    Low: 'var(--info)',
    Info: '#22C55E',
  };

  return (
    <div className="chartContainer">
      <div className="chartTitle">{title}</div>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Tooltip
            contentStyle={{
              background: 'rgba(16, 27, 47, 0.95)',
              border: '1px solid rgba(68, 215, 182, 0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
            itemStyle={{ color: 'var(--text)' }}
          />
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={72} outerRadius={96} paddingAngle={4}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={colors[entry.name] ?? 'var(--muted)'} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ServiceBarChart({ data, title, height = 280 }: { data: TrendDataPoint[]; title: string; height?: number }) {
  return (
    <div className="chartContainer">
      <div className="chartTitle">{title}</div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart layout="vertical" data={data} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} horizontal={false} />
          <XAxis type="number" stroke="var(--muted)" tickLine={false} axisLine={false} />
          <YAxis dataKey="day" type="category" width={100} stroke="var(--muted)" tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              background: 'rgba(16, 27, 47, 0.95)',
              border: '1px solid rgba(68, 215, 182, 0.24)',
              borderRadius: '10px',
            }}
            labelStyle={{ color: 'var(--text)' }}
            itemStyle={{ color: 'var(--text)' }}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[6, 6, 6, 6]} isAnimationActive={true} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
