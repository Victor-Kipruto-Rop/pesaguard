"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function AuthPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Authentication"
        title="Authentication"
        summary="Choose the sign-in or registration flow for your user journey."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/auth/login" className="secondaryBtn">Login</Link>
          <Link href="/auth/register" className="secondaryBtn">Register</Link>
          <Link href="/auth/forgot-password" className="secondaryBtn">Forgot password</Link>
          <Link href="/auth/verify-email" className="secondaryBtn">Verify email</Link>
          <Link href="/auth/two-factor-auth" className="secondaryBtn">Two-factor auth</Link>
        </div>
      </section>
    </main>
  );
}
