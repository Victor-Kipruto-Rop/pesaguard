'use client';

import { usePathname, useRouter } from 'next/navigation';
import type { Route } from 'next';
import { useEffect, useState } from 'react';

const PUBLIC_PREFIXES = [
  '/public',
  '/landing',
  '/pricing',
  '/about',
  '/blog',
  '/contact',
  '/security',
  '/legal',
  '/maintenance',
  '/docs',
];

const AUTH_PREFIXES = ['/auth'];

function isPublicRoute(pathname: string) {
  return PUBLIC_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function isAuthRoute(pathname: string) {
  return AUTH_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname() || '/';
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const publicRoute = isPublicRoute(pathname);
    const authRoute = isAuthRoute(pathname);
    const authenticated = typeof window !== 'undefined' && window.localStorage.getItem('pesaguard.auth') === 'true';

    if (!authenticated && !publicRoute && !authRoute) {
      router.replace('/auth/login' as Route);
      return;
    }

    if (authenticated && authRoute) {
      router.replace('/' as Route);
      return;
    }

    setReady(true);
  }, [pathname, router]);

  if (!ready) return null;
  return <>{children}</>;
}
