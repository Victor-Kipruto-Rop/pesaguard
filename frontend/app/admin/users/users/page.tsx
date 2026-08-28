'use client';

import PageHeader from '../../../../components/PageHeader';

export default function UsersPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Users" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Users</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
