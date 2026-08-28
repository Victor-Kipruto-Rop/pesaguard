"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { clearTokens } from '../../../lib/fetchAuth';

export default function LogoutPage() {
  const router = useRouter();
  useEffect(() => {
    // Call server logout which clears cookies, then redirect
    (async () => {
      try {
        await fetch('/api/auth/logout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, cache: 'no-store', credentials: 'include' });
      } catch (e) {
        // ignore
      }
      // small delay to allow clearing before redirect
      const t = setTimeout(() => router.replace('/auth/login'), 250);
      return () => clearTimeout(t);
    })();
  }, [router]);
  return <div className="muted">Signing out…</div>;
}
