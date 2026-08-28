"use client";
import React from 'react';
import Link from 'next/link';

export default function OnboardingLayout({ children, title, step, total }: { children: React.ReactNode; title?: string; step?: number; total?: number }) {
  return (
    <div className="onboarding-shell">
      <div className="onboarding-header">
        <div className="brand">
          <h2>PesaGuard</h2>
          <p className="muted">Premium setup — quick, secure, and modern</p>
        </div>
        <div className="progress-wrap">
          {typeof step === 'number' && typeof total === 'number' ? (
            <div className="progress">
              <div className="progress-bar" style={{ width: `${Math.round((step / total) * 100)}%` }} />
              <div className="progress-label">Step {step} of {total}</div>
            </div>
          ) : null}
        </div>
      </div>

      <main className="onboarding-main">
        <section className="onboarding-card">
          <header className="card-header">
            <h1>{title ?? 'Get started'}</h1>
            <nav className="card-actions">
              <a href="/help" className="ghost">Help</a>
            </nav>
          </header>
          <div className="card-body">{children}</div>
        </section>

        <aside className="onboarding-side">
          <div className="side-box">
            <h3>Need help?</h3>
            <p className="muted">Visit the help center or contact support for hands-on assistance.</p>
            <a href="/help" className="btn">Open Help</a>
          </div>
        </aside>
      </main>
    </div>
  );
}
