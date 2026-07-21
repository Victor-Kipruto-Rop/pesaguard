'use client';

import { usePathname } from 'next/navigation';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import OfflineBanner from './OfflineBanner';
import PublicNav from './PublicNav';

const PUBLIC_PREFIXES = [
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

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || '/';
  const publicRoute = isPublicRoute(pathname);
  const authRoute = isAuthRoute(pathname);

  if (publicRoute) {
    return (
      <div className="publicShell">
        <PublicNav />
        <OfflineBanner />
        <main className="publicMain">{children}</main>
      </div>
    );
  }

  if (authRoute) {
    return (
      <div className="authShell">
        <OfflineBanner />
        {children}
      </div>
    );
  }

  return (
    <div className="themeShell">
      <Sidebar />
      <div className="mainContent">
        <TopBar />
        <OfflineBanner />
        {children}
      </div>
    </div>
  );
}
