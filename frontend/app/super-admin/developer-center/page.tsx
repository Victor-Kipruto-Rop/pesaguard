"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminDeveloperCenterPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="Developer center"
        summary="Access platform integration controls, API activity, and developer tooling."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/integrations" className="secondaryBtn">Integrations</Link>
          <Link href="/super-admin/integrations/apis" className="secondaryBtn">APIs</Link>
          <Link href="/super-admin/integrations/webhooks" className="secondaryBtn">Webhooks</Link>
          <Link href="/super-admin/monitoring/api-monitor" className="secondaryBtn">API monitor</Link>
        </div>
      </section>
    </main>
  );
}
