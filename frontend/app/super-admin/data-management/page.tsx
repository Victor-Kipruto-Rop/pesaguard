"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminDataManagementPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Data management"
        summary="Track data movement, retention, and platform governance activities."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/monitoring/logs" className="secondaryBtn">Logs</Link>
          <Link href="/super-admin/monitoring/database-monitor" className="secondaryBtn">Database monitor</Link>
          <Link href="/super-admin/monitoring/error-tracking" className="secondaryBtn">Error tracking</Link>
          <Link href="/super-admin/settings" className="secondaryBtn">Settings</Link>
        </div>
      </section>
    </main>
  );
}
