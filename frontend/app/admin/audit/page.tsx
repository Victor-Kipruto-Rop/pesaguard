"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminAuditPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Audit & compliance"
        summary="Monitor audit trails, user activity, and policy compliance events."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/audit/audit-dashboard" className="secondaryBtn">Audit dashboard</Link>
          <Link href="/admin/audit/audit-logs" className="secondaryBtn">Audit logs</Link>
          <Link href="/admin/audit/transaction-audit" className="secondaryBtn">Transaction audit</Link>
          <Link href="/admin/audit/reconciliation-audit" className="secondaryBtn">Reconciliation audit</Link>
          <Link href="/admin/audit/user-audit" className="secondaryBtn">User audit</Link>
          <Link href="/admin/audit/compliance" className="secondaryBtn">Compliance</Link>
        </div>
      </section>
    </main>
  );
}
