'use client';

import PulseLine from './PulseLine';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  summary?: string;
  actions?: React.ReactNode;
  showPulse?: boolean;
}

export default function PageHeader({ eyebrow, title, summary, actions, showPulse = true }: PageHeaderProps) {
  return (
    <section className="hero pageHero">
      <div className="heroCopy">
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {summary ? <p className="muted">{summary}</p> : null}
        {showPulse ? <PulseLine className="pagePulse" height={28} /> : null}
        {actions ? <div className="heroActions">{actions}</div> : null}
      </div>
    </section>
  );
}
