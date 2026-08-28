'use client';

import PageHeader from '../../../../components/PageHeader';

export default function DocumentationPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Documentation" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Documentation</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
