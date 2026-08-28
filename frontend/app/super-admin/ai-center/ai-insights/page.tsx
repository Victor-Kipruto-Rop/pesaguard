"use client";

import PageHeader from '../../../../components/PageHeader';

export default function SuperAdminAiInsightsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Super admin"
        title="AI insights"
        summary="Review adoption, risk signals, recommendations, and anomaly summaries from AI-powered analysis."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 16 }}>
          <div>
            <h2>Insight overview</h2>
            <p className="muted">Track recommendations generated across transactions, customer risk, and operations.</p>
          </div>
          <div>
            <h2>Activity feed</h2>
            <p className="muted">See the latest AI-generated monitoring and decision support events.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
