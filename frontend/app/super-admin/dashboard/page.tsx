"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminDashboardPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Platform dashboard"
        summary="Overview of core platform health, customer activity, and operational KPIs."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin" className="secondaryBtn">Overview</Link>
          <Link href="/super-admin/monitoring" className="secondaryBtn">Monitoring</Link>
          <Link href="/super-admin/transactions" className="secondaryBtn">Transactions</Link>
          <Link href="/super-admin/customers" className="secondaryBtn">Customers</Link>
        </div>
      </section>
    </main>
  );
}
