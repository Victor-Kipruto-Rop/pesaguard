'use client';

import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';

interface AuthPageShellProps {
  eyebrow?: string;
  title: string;
  subtitle: string;
  badge?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  features?: string[];
}

export default function AuthPageShell({
  eyebrow = 'Premium access',
  title,
  subtitle,
  badge,
  children,
  footer,
  features = [
    'Enterprise-grade account security',
    'Fast reconciliation and risk review',
    'Operational visibility across teams',
  ],
}: AuthPageShellProps) {
  return (
    <main className="authPageShell">
      <div className="authFrame">
        <aside className="authSidePanel">
          <div className="authBrand">
            <span className="brandMark">PG</span>
            <div>
              <strong>PesaGuard</strong>
              <span>Protected operations</span>
            </div>
          </div>

          <div className="authSideHeader">
            <span className="eyebrow authEyebrow">{eyebrow}</span>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          <div className="authStatRow">
            <div className="authStatCard">
              <ShieldCheck size={18} />
              <span>Secure</span>
            </div>
            <div className="authStatCard">
              <Sparkles size={18} />
              <span>Premium</span>
            </div>
          </div>

          <ul className="authFeatureList">
            {features.map((feature) => (
              <li key={feature}>
                <CheckCircle2 size={18} />
                <span>{feature}</span>
              </li>
            ))}
          </ul>

          {badge ? <div className="authBadge">{badge}</div> : null}
        </aside>

        <section className="authPanel">
          <div className="authPanelInner">{children}</div>
          {footer ? <div className="authFooter">{footer}</div> : null}
        </section>
      </div>
    </main>
  );
}
