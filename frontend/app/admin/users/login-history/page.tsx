'use client';

import PageHeader from '../../../../components/PageHeader';

export default function LoginHistoryPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Login History" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Login History</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
