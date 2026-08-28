'use client';

import PageHeader from '../../../../components/PageHeader';

export default function TransactionDetailsPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Transaction Details" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Transaction Details</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
