'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const authenticated = typeof window !== 'undefined' && window.localStorage.getItem('pesaguard.auth') === 'true';
    if (!authenticated && pathname !== '/auth/login') {
      router.replace('/auth/login');
      return;
    }
    setReady(true);
  }, [pathname, router]);

  if (!ready) return null;
  return <>{children}</>;
}
