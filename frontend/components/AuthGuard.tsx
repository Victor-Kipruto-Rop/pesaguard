"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

// Instead of reading tokens from localStorage, call server `/api/auth/me` to
// validate session via HttpOnly cookie.

async function checkSession(): Promise<boolean> {
  try {
    const res = await fetch('/api/auth/me', { method: 'GET', cache: 'no-store', credentials: 'include' });
    return res.ok;
  } catch (e) {
    return false;
  }
}

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    checkSession().then((ok) => {
      if (!mounted) return;
      setLoading(false);
      if (!ok) router.replace('/auth/login');
    });
    return () => {
      mounted = false;
    };
  }, [router]);

  if (loading) return <div className="muted">Checking session…</div>;
  return <>{children}</>;
}
