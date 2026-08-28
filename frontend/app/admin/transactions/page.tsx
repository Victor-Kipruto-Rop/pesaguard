"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminTransactionsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Transactions"
        summary="Track incoming, outgoing, failed, and search-driven transaction activity."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/transactions/all-transactions" className="secondaryBtn">All transactions</Link>
          <Link href="/admin/transactions/incoming-transactions" className="secondaryBtn">Incoming transactions</Link>
          <Link href="/admin/transactions/outgoing-transactions" className="secondaryBtn">Outgoing transactions</Link>
          <Link href="/admin/transactions/failed-transactions" className="secondaryBtn">Failed transactions</Link>
          <Link href="/admin/transactions/pending-transactions" className="secondaryBtn">Pending transactions</Link>
          <Link href="/admin/transactions/transaction-history" className="secondaryBtn">Transaction history</Link>
          <Link href="/admin/transactions/search-transactions" className="secondaryBtn">Search transactions</Link>
        </div>
      </section>
    </main>
  );
}
