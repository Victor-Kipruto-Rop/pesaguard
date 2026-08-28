'use client';

import PageHeader from '../../../../components/PageHeader';

export default function PaymentGatewaysPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Super admin" title="Payment Gateways" summary="Operational controls and management views for this PesaGuard module." />
      <section className="card">
        <div className="sectionTitle">Payment Gateways</div>
        <p className="muted" style={{ marginTop: 12 }}>
          This area is ready for production workflows, role-based actions, approvals, and reporting for payment gateways.
        </p>
      </section>
    </main>
  );
}
