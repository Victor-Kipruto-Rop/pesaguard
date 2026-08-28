"use client";

import PageHeader from '../../../../components/PageHeader';

export default function SuperAdminAiConfigurationPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="AI configuration"
        summary="Configure the platform's AI models, governance rules, and feature enablement."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 16 }}>
          <div>
            <h2>Model settings</h2>
            <p className="muted">Tune generative and predictive settings for the tenant platform.</p>
          </div>
          <div>
            <h2>Governance</h2>
            <p className="muted">Control review workflows, approvals, and prompt safeguards.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
