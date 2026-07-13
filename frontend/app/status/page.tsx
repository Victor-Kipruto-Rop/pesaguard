'use client';

const components = [
  { name: 'Webhook ingestion', status: 'Operational', detail: 'Incoming callbacks are being processed with low latency.' },
  { name: 'Reconciliation engine', status: 'Operational', detail: 'Discrepancy detection and matching remain fully active.' },
  { name: 'Alert delivery', status: 'Operational', detail: 'Notifications are routed with deduplication and severity-aware handling.' },
  { name: 'Backup and retention', status: 'Scheduled', detail: 'Daily backup jobs and retention enforcement are running as planned.' },
];

const updates = [
  { title: 'Monitoring coverage', message: 'All critical services are being observed with automated alerts and incident escalation.', time: '2 min ago' },
  { title: 'Backup automation', message: 'The latest backup cycle completed successfully and is retained per policy.', time: '45 min ago' },
  { title: 'Support readiness', message: 'Support channels and incident workflows are active for pilot customers.', time: '2 hrs ago' },
];

const highlights = [
  { title: 'Operational transparency', body: 'A consistent status experience ensures pilot stakeholders always understand service health.' },
  { title: 'Governance readiness', body: 'Backup automation, retention enforcement, and response workflows are documented and active.' },
  { title: 'Customer confidence', body: 'The experience is designed for investor, compliance, and pilot-customer review.' },
];

export default function StatusPage() {
  return (
    <main className="pageShell">
      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">Premium readiness pack</div>
          <p className="eyebrow">Pilot Service Status</p>
          <h1>Reliable, transparent operations for every pilot customer</h1>
          <p className="muted">PesaGuard is operating normally, with service monitoring, backup automation, retention enforcement, and incident response controls active across the platform.</p>
          <div className="heroActions">
            <a className="primaryBtn" href="/support">Open support</a>
            <a className="secondaryBtn" href="/agreements">Review pilot terms</a>
          </div>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">Signal</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="grid twoUp">
        <div className="panel">
          <h2>Current service health</h2>
          <ul className="stackList">
            {components.map((item) => (
              <li key={item.name}>
                <strong>{item.name}</strong>
                <div className="muted" style={{ marginTop: 4 }}>{item.detail}</div>
                <div style={{ marginTop: 8 }}><span className={`pill ${item.status === 'Scheduled' ? 'warning' : 'ok'}`}>{item.status}</span></div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Operational posture</h2>
          <ul className="stackList">
            <li>Daily backup automation enabled and verified</li>
            <li>Restore validation is prepared for pilot environment testing</li>
            <li>Incident response workflow remains active for critical events</li>
            <li>Support and status communications are synchronized for customers</li>
          </ul>
        </div>
      </section>

      <section className="panel">
        <div className="sectionHeader">
          <h2>Recent updates</h2>
          <div className="heroBadge compact">Live</div>
        </div>
        <div className="stackList">
          {updates.map((item) => (
            <div key={item.title} className="feedItem">
              <div className="feedHeader">
                <strong>{item.title}</strong>
                <span className="muted small">{item.time}</span>
              </div>
              <div className="muted">{item.message}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Downloadable readiness assets</h2>
        <div className="downloadRow">
          <a className="primaryBtn" href="/assets/readiness-pack-summary.txt" download>Download readiness summary</a>
          <a className="secondaryBtn" href="/assets/support-readiness-brief.txt" download>Download support brief</a>
        </div>
      </section>
    </main>
  );
}
