'use client';

import PageHeader from '../../../../components/PageHeader';

export default function ProfilePage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Profile" summary="Tenant administration view for this module." />
      <section className="card">
        <div className="sectionTitle">Profile</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This page is ready for tenant-focused admin workflows, rules, and reporting.
        </p>
      </section>
    </main>
  );
}
