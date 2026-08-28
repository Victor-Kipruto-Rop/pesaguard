"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminOrganizationsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Organizations"
        summary="Manage organization-level configuration and tenant view across the platform."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/customers" className="secondaryBtn">Customers</Link>
          <Link href="/super-admin/settings/organization-settings" className="secondaryBtn">Organization settings</Link>
          <Link href="/super-admin/users" className="secondaryBtn">Users</Link>
          <Link href="/super-admin/reports" className="secondaryBtn">Reports</Link>
        </div>
      </section>
    </main>
  );
}
