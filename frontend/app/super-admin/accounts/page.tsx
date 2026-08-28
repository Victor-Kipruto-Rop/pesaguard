"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminAccountsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Accounts"
        summary="Review and manage customer, system, and organization account activity."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/customers" className="secondaryBtn">Customers</Link>
          <Link href="/super-admin/users" className="secondaryBtn">Users</Link>
          <Link href="/super-admin/organizations" className="secondaryBtn">Organizations</Link>
          <Link href="/super-admin/reports" className="secondaryBtn">Reports</Link>
          <Link href="/super-admin/settings" className="secondaryBtn">Settings</Link>
        </div>
      </section>
    </main>
  );
}
