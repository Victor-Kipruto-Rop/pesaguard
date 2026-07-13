'use client';

const policyItems = [
  {
    title: 'Privacy policy',
    summary: 'Explains how customer and payer data is collected, used, retained, and deleted.',
    href: '/assets/privacy-policy.txt',
  },
  {
    title: 'Data retention',
    summary: 'Defines retention windows, backup handling, and offboarding disposal processes.',
    href: '/assets/readiness-pack-summary.txt',
  },
  {
    title: 'Security policy',
    summary: 'Summarizes controls for access, monitoring, logging, and response readiness.',
    href: '/assets/support-readiness-brief.txt',
  },
];

const highlights = [
  { title: 'Trust architecture', body: 'Policies are structured to support pilot onboarding and compliance conversations.' },
  { title: 'Data discipline', body: 'Retention and deletion expectations are clearly documented and operationalized.' },
  { title: 'Control maturity', body: 'Security and support practices appear consistent, explicit, and reviewable.' },
];

export default function PoliciesPage() {
  return (
    <main className="pageShell">
      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">Premium policy suite</div>
          <p className="eyebrow">Policies & Controls</p>
          <h1>Operational policies that reinforce trust and compliance</h1>
          <p className="muted">These policy views make your governance posture clear to pilots, investors, and compliance reviewers.</p>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">Control</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Policy library</h2>
        <div className="grid">
          {policyItems.map((item) => (
            <article key={item.title} className="assetCard">
              <div className="eyebrow">Policy</div>
              <h3>{item.title}</h3>
              <p className="muted">{item.summary}</p>
              <div className="downloadRow">
                <a className="primaryBtn" href={item.href} download>Download</a>
                <a className="secondaryBtn" href={item.href}>Open</a>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
