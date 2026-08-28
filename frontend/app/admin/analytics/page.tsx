"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminAnalyticsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Analytics"
        summary="Explore revenue, performance, reconciliation, and transaction analytics."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/analytics/analytics-dashboard" className="secondaryBtn">Analytics dashboard</Link>
          <Link href="/admin/analytics/revenue-analytics" className="secondaryBtn">Revenue analytics</Link>
          <Link href="/admin/analytics/transaction-analytics" className="secondaryBtn">Transaction analytics</Link>
          <Link href="/admin/analytics/performance-metrics" className="secondaryBtn">Performance metrics</Link>
          <Link href="/admin/analytics/trends" className="secondaryBtn">Trends</Link>
          <Link href="/admin/analytics/member-analytics" className="secondaryBtn">Member analytics</Link>
        </div>
      </section>
    </main>
  );
}
