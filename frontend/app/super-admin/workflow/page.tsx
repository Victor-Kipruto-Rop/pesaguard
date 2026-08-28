"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminWorkflowPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Workflow controls"
        summary="Manage automation rules, queues, and delivery workflows across the platform."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/settings/automation-rules" className="secondaryBtn">Automation rules</Link>
          <Link href="/super-admin/reconciliation" className="secondaryBtn">Reconciliation</Link>
          <Link href="/super-admin/monitoring/queue-monitor" className="secondaryBtn">Queue monitor</Link>
          <Link href="/super-admin/feature-flags" className="secondaryBtn">Feature flags</Link>
        </div>
      </section>
    </main>
  );
}
