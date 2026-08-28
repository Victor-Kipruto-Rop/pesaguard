"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminSecurityPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Security"
        summary="Inspect system security posture, governance controls, and compliance signals."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/audit-compliance" className="secondaryBtn">Audit & compliance</Link>
          <Link href="/super-admin/settings" className="secondaryBtn">Settings</Link>
          <Link href="/super-admin/monitoring/server-monitor" className="secondaryBtn">Server monitor</Link>
          <Link href="/super-admin/monitoring/error-tracking" className="secondaryBtn">Error tracking</Link>
        </div>
      </section>
    </main>
  );
}
