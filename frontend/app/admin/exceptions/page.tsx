"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminExceptionsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Exceptions"
        summary="Review and resolve mismatches, escalations, and pending exception queues."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/exceptions/open-exceptions" className="secondaryBtn">Open exceptions</Link>
          <Link href="/admin/exceptions/pending-review" className="secondaryBtn">Pending review</Link>
          <Link href="/admin/exceptions/resolved-exceptions" className="secondaryBtn">Resolved exceptions</Link>
          <Link href="/admin/exceptions/escalation-center" className="secondaryBtn">Escalation center</Link>
          <Link href="/admin/exceptions/exception-details" className="secondaryBtn">Exception details</Link>
          <Link href="/admin/exceptions/account-mismatches" className="secondaryBtn">Account mismatches</Link>
        </div>
      </section>
    </main>
  );
}
