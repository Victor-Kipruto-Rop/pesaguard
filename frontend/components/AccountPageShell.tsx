'use client';

import type { ReactNode } from 'react';

interface AccountPageShellProps {
  title: string;
  subtitle: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function AccountPageShell({ title, subtitle, actions, children }: AccountPageShellProps) {
  return (
    <main className="shell accountShell">
      <section className="accountHero fadeInUp">
        <div className="heroCopy">
          <p className="eyebrow">Account settings</p>
          <h1>{title}</h1>
          <p className="muted">{subtitle}</p>
        </div>
        {actions ? <div className="heroActions">{actions}</div> : null}
      </section>
      <div className="accountBody">{children}</div>
    </main>
  );
}
