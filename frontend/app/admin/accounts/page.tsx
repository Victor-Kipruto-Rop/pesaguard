"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminAccountsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Accounts"
        summary="Review member financial records, balances, statements, and account history."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/accounts/balances" className="secondaryBtn">Balances</Link>
          <Link href="/admin/accounts/bank-accounts" className="secondaryBtn">Bank accounts</Link>
          <Link href="/admin/accounts/mpesa-accounts" className="secondaryBtn">M-Pesa accounts</Link>
          <Link href="/admin/accounts/wallets" className="secondaryBtn">Wallets</Link>
          <Link href="/admin/accounts/account-history" className="secondaryBtn">Account history</Link>
          <Link href="/admin/accounts/account-statements" className="secondaryBtn">Statements</Link>
          <Link href="/admin/accounts/ledgers" className="secondaryBtn">Ledgers</Link>
        </div>
      </section>
    </main>
  );
}
