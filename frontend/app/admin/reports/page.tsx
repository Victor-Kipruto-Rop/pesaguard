"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminReportsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Reports"
        summary="Generate scheduled and ad-hoc operational and financial reports."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/reports/reports-dashboard" className="secondaryBtn">Reports dashboard</Link>
          <Link href="/admin/reports/daily-report" className="secondaryBtn">Daily report</Link>
          <Link href="/admin/reports/weekly-report" className="secondaryBtn">Weekly report</Link>
          <Link href="/admin/reports/monthly-report" className="secondaryBtn">Monthly report</Link>
          <Link href="/admin/reports/transaction-report" className="secondaryBtn">Transaction report</Link>
          <Link href="/admin/reports/exception-report" className="secondaryBtn">Exception report</Link>
          <Link href="/admin/reports/scheduled-reports" className="secondaryBtn">Scheduled reports</Link>
        </div>
      </section>
    </main>
  );
}
