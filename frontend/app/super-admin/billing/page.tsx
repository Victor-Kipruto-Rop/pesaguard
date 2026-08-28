"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminBillingPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Billing"
        summary="Review commercial and billing controls at the platform layer."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/settings" className="secondaryBtn">Platform settings</Link>
          <Link href="/super-admin/reports" className="secondaryBtn">Platform reports</Link>
          <Link href="/super-admin/customers" className="secondaryBtn">Customer portfolio</Link>
        </div>
      </section>
    </main>
  );
}
