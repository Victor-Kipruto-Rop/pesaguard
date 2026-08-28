'use client';

import PageHeader from '../../../../components/PageHeader';

export default function SecurityPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Security" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Security</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
