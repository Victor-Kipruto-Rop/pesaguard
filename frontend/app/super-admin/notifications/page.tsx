"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminNotificationsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Notifications"
        summary="Manage policy and platform-wide notifications for clients and admins."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/support" className="secondaryBtn">Support</Link>
          <Link href="/super-admin/help-center" className="secondaryBtn">Help center</Link>
          <Link href="/super-admin/settings" className="secondaryBtn">Settings</Link>
          <Link href="/super-admin/customers" className="secondaryBtn">Customers</Link>
        </div>
      </section>
    </main>
  );
}
