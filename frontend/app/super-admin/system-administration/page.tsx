"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminSystemAdministrationPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="System administration"
        summary="Access operational controls for platform configuration and health management."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/settings" className="secondaryBtn">Settings</Link>
          <Link href="/super-admin/monitoring" className="secondaryBtn">Monitoring</Link>
          <Link href="/super-admin/feature-flags" className="secondaryBtn">Feature flags</Link>
          <Link href="/super-admin/audit-log" className="secondaryBtn">Audit log</Link>
        </div>
      </section>
    </main>
  );
}
