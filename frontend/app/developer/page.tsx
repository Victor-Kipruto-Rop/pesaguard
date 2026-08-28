"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function DeveloperPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Developer"
        title="Developer portal"
        summary="Use the API reference, webhooks, examples, onboarding, and sandbox tools."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/developer/developer-home" className="secondaryBtn">Developer home</Link>
          <Link href="/developer/api-reference" className="secondaryBtn">API reference</Link>
          <Link href="/developer/authentication" className="secondaryBtn">Authentication</Link>
          <Link href="/developer/webhooks" className="secondaryBtn">Webhooks</Link>
          <Link href="/developer/examples" className="secondaryBtn">Examples</Link>
          <Link href="/developer/sandbox" className="secondaryBtn">Sandbox</Link>
        </div>
      </section>
    </main>
  );
}
