"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminPaymentsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Payments"
        summary="Track platform payment flows and operational bank or gateway activity."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/integrations/payment-gateways" className="secondaryBtn">Payment gateways</Link>
          <Link href="/super-admin/integrations/banks" className="secondaryBtn">Banks</Link>
          <Link href="/super-admin/integrations/mpesa" className="secondaryBtn">M-Pesa</Link>
          <Link href="/super-admin/transactions" className="secondaryBtn">Transactions</Link>
        </div>
      </section>
    </main>
  );
}
