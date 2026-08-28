'use client';

import PageHeader from '../../../../components/PageHeader';

export default function CurrencyMismatchesPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Currency Mismatches" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Currency Mismatches</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
