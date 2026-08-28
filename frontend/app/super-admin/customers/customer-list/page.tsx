'use client';

import PageHeader from '../../../../components/PageHeader';

export default function CustomerListPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Super admin" title="Customer List" summary="Operational controls and management views for this PesaGuard module." />
      <section className="card">
        <div className="sectionTitle">Customer List</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This area is ready for production workflows, role-based actions, approvals, and reporting for customer list.
        </p>
      </section>
    </main>
  );
}
