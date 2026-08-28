'use client';

import PageHeader from '../../../../components/PageHeader';

export default function CustomerActivityPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Super admin" title="Customer Activity" summary="Operational controls and management views for this PesaGuard module." />
      <section className="card">
        <div className="sectionTitle">Customer Activity</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This area is ready for production workflows, role-based actions, approvals, and reporting for customer activity.
        </p>
      </section>
    </main>
  );
}
