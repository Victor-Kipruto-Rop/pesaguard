"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminDashboardPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Dashboards"
        summary="Jump into operational views for daily monitoring and executive oversight."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/dashboard/dashboard" className="secondaryBtn">Dashboard</Link>
          <Link href="/admin/dashboard/executive-dashboard" className="secondaryBtn">Executive dashboard</Link>
          <Link href="/admin/dashboard/performance-overview" className="secondaryBtn">Performance overview</Link>
          <Link href="/admin/dashboard/realtime-dashboard" className="secondaryBtn">Realtime dashboard</Link>
        </div>
      </section>
    </main>
  );
}
