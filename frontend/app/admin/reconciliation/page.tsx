"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminReconciliationPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Reconciliation"
        summary="Review manual, automatic, and dashboard-based reconciliation tasks."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/reconciliation/reconciliation-dashboard" className="secondaryBtn">Reconciliation dashboard</Link>
          <Link href="/admin/reconciliation/daily-reconciliation" className="secondaryBtn">Daily reconciliation</Link>
          <Link href="/admin/reconciliation/approval-queue" className="secondaryBtn">Approval queue</Link>
          <Link href="/admin/reconciliation/manual-reconciliation" className="secondaryBtn">Manual reconciliation</Link>
          <Link href="/admin/reconciliation/automatic-reconciliation" className="secondaryBtn">Automatic reconciliation</Link>
          <Link href="/admin/reconciliation/reconciliation-history" className="secondaryBtn">History</Link>
        </div>
      </section>
    </main>
  );
}
