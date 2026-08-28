"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminAnalyticsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Analytics"
        summary="Monitor overall platform trends, adoption, and operational health."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/reports" className="secondaryBtn">Reports</Link>
          <Link href="/super-admin/monitoring" className="secondaryBtn">Monitoring</Link>
          <Link href="/super-admin/transactions" className="secondaryBtn">Transactions</Link>
          <Link href="/super-admin/audit-compliance" className="secondaryBtn">Audit compliance</Link>
          <Link href="/super-admin/feature-flags" className="secondaryBtn">Feature flags</Link>
        </div>
      </section>
    </main>
  );
}
