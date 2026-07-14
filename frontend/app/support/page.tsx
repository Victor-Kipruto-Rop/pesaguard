'use client';

const supportChannels = [
  { label: 'Email', value: 'pilot-support@pesaguard.example', detail: 'Best for onboarding questions, policy requests, and non-urgent issues.' },
  { label: 'Priority incident channel', value: '#pesaguard-pilot', detail: 'Fastest route for live incidents and customer-impacting issues.' },
  { label: 'Status updates', value: '/status', detail: 'Review the current service posture and recent operational notices.' },
];

const slaLevels = [
  { title: 'Critical', target: '15 mins', detail: 'Production outage, failed reconciliation, or material customer-impacting incident.' },
  { title: 'High', target: '1 hour', detail: 'Severe degradation affecting a key workflow or tenant experience.' },
  { title: 'Medium', target: '4 hours', detail: 'Non-blocking issue requiring investigation or workflow guidance.' },
];

const highlights = [
  { title: 'Fast triage', body: 'Every report is routed through a defined support workflow with clear ownership.' },
  { title: 'Transparent escalation', body: 'Critical incidents receive immediate attention and customer-visible updates.' },
  { title: 'Operational continuity', body: 'The support model is aligned with incident response and reporting standards.' },
];

export default function SupportPage() {
  return (
    <main className="pageShell">
      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">Premium support readiness</div>
          <p className="eyebrow">Pilot Support</p>
          <h1>Fast, expert support for every rollout stage</h1>
          <p className="muted">Use the pilot support workspace to raise incidents, review status updates, and coordinate onboarding with the PesaGuard team. We also validate localized alerting and customer-facing messaging during pilot scope reviews.</p>
          <div className="heroActions">
            <a className="primaryBtn" href="mailto:pilot-support@pesaguard.example">Email support</a>
            <a className="secondaryBtn" href="/status">View live status</a>
          </div>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">Support promise</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="grid twoUp">
        <div className="panel">
          <h2>Support channels</h2>
          <div className="stackList">
            {supportChannels.map((item) => (
              <div key={item.label} className="feedItem">
                <div className="feedHeader">
                  <strong>{item.label}</strong>
                </div>
                <div className="muted" style={{ marginBottom: 4 }}>{item.value}</div>
                <div className="muted">{item.detail}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          <h2>What to include in your report</h2>
          <ul className="stackList">
            <li>Tenant or environment name</li>
            <li>Time of incident and affected workflow</li>
            <li>Relevant transaction or discrepancy IDs</li>
            <li>Any screenshots, webhook samples, or export data needed for triage</li>
          </ul>
        </div>
      </section>

      <section className="panel">
        <h2>Response targets</h2>
        <div className="grid">
          {slaLevels.map((item) => (
            <div key={item.title} className="panel">
              <div className="eyebrow">{item.title}</div>
              <h3>{item.target}</h3>
              <div className="muted">{item.detail}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Downloadable support assets</h2>
        <div className="downloadRow">
          <a className="primaryBtn" href="/assets/support-readiness-brief.txt" download>Download support brief</a>
          <a className="secondaryBtn" href="/assets/readiness-pack-summary.txt" download>Download readiness summary</a>
        </div>
      </section>
    </main>
  );
}
