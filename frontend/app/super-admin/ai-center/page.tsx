"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function SuperAdminAiCenterPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="AI center"
        summary="Review AI-driven insights, configuration, and platform automation controls."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/super-admin/ai-center/ai-configuration" className="secondaryBtn">
            AI configuration
          </Link>
          <Link href="/super-admin/ai-center/ai-insights" className="secondaryBtn">
            AI insights
          </Link>
        </div>
      </section>
    </main>
  );
}
