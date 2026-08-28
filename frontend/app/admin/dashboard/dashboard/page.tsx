'use client';

import PageHeader from '../../../../components/PageHeader';

export default function DashboardPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Dashboard" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Dashboard</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
