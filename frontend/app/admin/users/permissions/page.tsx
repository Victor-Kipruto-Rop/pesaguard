'use client';

import PageHeader from '../../../../components/PageHeader';

export default function PermissionsPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Permissions" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Permissions</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
