"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function AccountPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Account"
        title="Account center"
        summary="Manage your profile, security settings, and connected sessions."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/account/profile" className="secondaryBtn">Profile</Link>
          <Link href="/account/security" className="secondaryBtn">Security</Link>
          <Link href="/account/active-sessions" className="secondaryBtn">Active sessions</Link>
          <Link href="/account/api-tokens" className="secondaryBtn">API tokens</Link>
          <Link href="/account/preferences" className="secondaryBtn">Preferences</Link>
        </div>
      </section>
    </main>
  );
}
