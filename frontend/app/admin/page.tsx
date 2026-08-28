'use client';

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function TenantAdminPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Tenant admin"
        title="Tenant administration"
        summary="Configure SACCO settings, monitor tenant health, and access tenant support tools."
      />

      <section className="card" style={{ display: 'grid', gap: 16 }}>
        <div>
          <h2>Tenant controls</h2>
          <p className="muted">
            This workspace is intended for tenant-level administration and operational support. Use the tenant settings, support, and compliance tools available below.
          </p>
        </div>

        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/settings" className="primaryBtn">
            Tenant settings
          </Link>
          <Link href="/admin/support" className="secondaryBtn">
            Contact support
          </Link>
          <Link href="/super-admin" className="secondaryBtn">
            View super-admin console
          </Link>
        </div>
      </section>
    </main>
  );
}
