'use client';

const agreements = [
  {
    title: 'Pilot agreement',
    summary: 'Defines scope, duration, support expectations, and pilot termination criteria.',
    href: '/assets/pilot-agreement.txt',
  },
  {
    title: 'Terms of service',
    summary: 'Outlines service boundaries, customer responsibilities, and support commitments.',
    href: '/assets/terms-of-service.txt',
  },
  {
    title: 'Data processing agreement',
    summary: 'Clarifies data handling, security expectations, and deletion responsibilities.',
    href: '/assets/data-processing-agreement.txt',
  },
];

const highlights = [
  { title: 'Commercial clarity', body: 'Pilot terms are easy to review and align with customer expectations.' },
  { title: 'Audit readiness', body: 'Documented terms strengthen compliance review and procurement discussions.' },
  { title: 'Operational confidence', body: 'The agreement pack supports trust with clear escalation and support posture.' },
];

export default function AgreementsPage() {
  return (
    <main className="pageShell">
      <section className="hero panel readinessHero">
        <div className="heroCopy">
          <div className="heroBadge">Premium agreement pack</div>
          <p className="eyebrow">Pilot Agreements</p>
          <h1>Clear commercial and operating terms for pilot customers</h1>
          <p className="muted">These materials provide a dependable foundation for customer trust, compliance review, and onboarding conversations.</p>
        </div>
      </section>

      <section className="readinessGrid">
        {highlights.map((item) => (
          <article key={item.title} className="assetCard">
            <div className="eyebrow">Value</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.body}</p>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Agreement pack</h2>
        <div className="grid">
          {agreements.map((item) => (
            <article key={item.title} className="assetCard">
              <div className="eyebrow">Draft</div>
              <h3>{item.title}</h3>
              <p className="muted">{item.summary}</p>
              <div className="downloadRow">
                <a className="primaryBtn" href={item.href} download>Download</a>
                <a className="secondaryBtn" href={item.href}>Preview</a>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
