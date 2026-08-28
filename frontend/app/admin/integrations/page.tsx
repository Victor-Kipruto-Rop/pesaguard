"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminIntegrationsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Integrations"
        summary="Manage external financial and technical integrations for the tenant."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/integrations/integration-dashboard" className="secondaryBtn">Integration dashboard</Link>
          <Link href="/admin/integrations/mpesa" className="secondaryBtn">M-Pesa</Link>
          <Link href="/admin/integrations/banks" className="secondaryBtn">Banks</Link>
          <Link href="/admin/integrations/api-keys" className="secondaryBtn">API keys</Link>
          <Link href="/admin/integrations/webhooks" className="secondaryBtn">Webhooks</Link>
          <Link href="/admin/integrations/integration-logs" className="secondaryBtn">Integration logs</Link>
          <Link href="/admin/integrations/callbacks" className="secondaryBtn">Callbacks</Link>
        </div>
      </section>
    </main>
  );
}
