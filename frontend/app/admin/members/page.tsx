"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminMembersPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Members"
        summary="Browse member records, KYC state, accounts, and activity events."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/members/members-list" className="secondaryBtn">Members list</Link>
          <Link href="/admin/members/member-profile" className="secondaryBtn">Member profile</Link>
          <Link href="/admin/members/kyc" className="secondaryBtn">KYC</Link>
          <Link href="/admin/members/member-accounts" className="secondaryBtn">Member accounts</Link>
          <Link href="/admin/members/member-documents" className="secondaryBtn">Member documents</Link>
          <Link href="/admin/members/member-activity" className="secondaryBtn">Member activity</Link>
          <Link href="/admin/members/member-transactions" className="secondaryBtn">Member transactions</Link>
        </div>
      </section>
    </main>
  );
}
