"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminPaymentsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Payments"
        summary="Track transactions, disbursements, refunds, and payment workflows."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/payments/payment-dashboard" className="secondaryBtn">Payment dashboard</Link>
          <Link href="/admin/payments/payment-history" className="secondaryBtn">Payment history</Link>
          <Link href="/admin/payments/mpesa-payments" className="secondaryBtn">M-Pesa payments</Link>
          <Link href="/admin/payments/bank-transfers" className="secondaryBtn">Bank transfers</Link>
          <Link href="/admin/payments/disbursements" className="secondaryBtn">Disbursements</Link>
          <Link href="/admin/payments/refunds" className="secondaryBtn">Refunds</Link>
          <Link href="/admin/payments/scheduled-payments" className="secondaryBtn">Scheduled payments</Link>
        </div>
      </section>
    </main>
  );
}
