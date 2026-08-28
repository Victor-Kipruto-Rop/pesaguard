"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminExceptionsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Exceptions"
        summary="Review platform-wide exceptions and operational escalations."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/reconciliation" className="secondaryBtn">Reconciliation</Link>
          <Link href="/super-admin/monitoring/error-tracking" className="secondaryBtn">Error tracking</Link>
          <Link href="/super-admin/monitoring/logs" className="secondaryBtn">Logs</Link>
          <Link href="/super-admin/transactions" className="secondaryBtn">Transactions</Link>
        </div>
      </section>
    </main>
  );
}
