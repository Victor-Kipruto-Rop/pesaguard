"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function OnboardingPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Onboarding"
        title="Onboarding flow"
        summary="Complete setup tasks for organization creation, verification, and configuration."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/onboarding/welcome" className="secondaryBtn">Welcome</Link>
          <Link href="/onboarding/create-organization" className="secondaryBtn">Create organization</Link>
          <Link href="/onboarding/verify-organization" className="secondaryBtn">Verify organization</Link>
          <Link href="/onboarding/upload-documents" className="secondaryBtn">Upload documents</Link>
          <Link href="/onboarding/configure-reconciliation" className="secondaryBtn">Configure reconciliation</Link>
          <Link href="/onboarding/complete-setup" className="secondaryBtn">Complete setup</Link>
        </div>
      </section>
    </main>
  );
}
