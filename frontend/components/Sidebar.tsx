'use client';

import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { useLocale } from '../lib/i18n';

function IconBase({ children }: { children: ReactNode }) {
  return (
    <span className="icon" aria-hidden="true">
      {children}
    </span>
  );
}

function NavIcon({ d }: { d: string }) {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d={d} />
      </svg>
    </IconBase>
  );
}

interface NavItem {
  href: string;
  labelKey: string;
  icon: string;
}

const CORE_NAV: NavItem[] = [
  { href: '/', labelKey: 'sidebar.dashboard', icon: 'M4 19h16 M7 15v-4 M12 15V7 M17 15v-2' },
  { href: '/transactions', labelKey: 'sidebar.transactions', icon: 'M4 7h16 M4 12h16 M4 17h10' },
  { href: '/reconciliation', labelKey: 'sidebar.reconciliation', icon: 'M8 7h8 M8 12h5 M8 17h8 M16 7l3 3-3 3' },
  { href: '/anomalies', labelKey: 'sidebar.anomalies', icon: 'M12 9v4 M12 17h.01 M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z' },
  { href: '/health', labelKey: 'sidebar.health', icon: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z M9 12l2 2 4-4' },
  { href: '/notifications', labelKey: 'sidebar.notifications', icon: 'M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5 M9.5 17a2.5 2.5 0 0 0 5 0' },
  { href: '/reports', labelKey: 'sidebar.reports', icon: 'M4 19V9 M10 19V5 M16 19v-7 M22 19H2' },
  { href: '/account', labelKey: 'sidebar.account', icon: 'M12 3v2 M12 19v2 M4.2 7.2l1.4 1.4 M18.4 15.4l1.4 1.4 M3 12h2 M19 12h2 M4.2 16.8l1.4-1.4 M18.4 8.6l1.4-1.4 M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z' },
  { href: '/audit-log', labelKey: 'sidebar.auditLog', icon: 'M7 3h8l4 4v14H7z M15 3v5h5 M9 13h6 M9 17h4' },
];

const PILOT_NAV: NavItem[] = [
  { href: '/onboarding', labelKey: 'sidebar.onboarding', icon: 'M5 12h14 M12 5l7 7-7 7' },
  { href: '/feedback', labelKey: 'sidebar.feedback', icon: 'M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z' },
  { href: '/sandbox', labelKey: 'sidebar.sandbox', icon: 'M4 7h16v10H4z M8 21h8' },
];

const MORE_NAV: NavItem[] = [
  { href: '/insights', labelKey: 'sidebar.insights', icon: 'M4 19V9 M10 19V5 M16 19v-7 M22 19H2' },
  { href: '/tools', labelKey: 'sidebar.tools', icon: 'M14 4l6 6 M8 20l-4-4 8-8 4 4Z' },
  { href: '/status', labelKey: 'sidebar.status', icon: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z M9 12l2 2 4-4' },
  { href: '/support', labelKey: 'sidebar.support', icon: 'M12 20a8 8 0 1 0-8-8v1.5a1.5 1.5 0 0 0 3 0V8a5 5 0 1 1 5 5 M12 22v-2' },
  { href: '/docs', labelKey: 'sidebar.docs', icon: 'M7 3h8l4 4v14H7z M15 3v5h5' },
  { href: '/settings', labelKey: 'sidebar.settings', icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z' },
];

const ADMIN_NAV: NavItem[] = [
  { href: '/admin', labelKey: 'sidebar.admin', icon: 'M4 19h16 M7 15v-4 M12 15V7 M17 15v-2' },
  { href: '/admin/customers', labelKey: 'sidebar.customers', icon: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75' },
  { href: '/admin/monitoring', labelKey: 'sidebar.monitoring', icon: 'M2 12h4l2-7 4 14 2-7h8' },
  { href: '/admin/feature-flags', labelKey: 'sidebar.featureFlags', icon: 'M4 7h16 M4 12h10 M4 17h6' },
  { href: '/admin/audit-log', labelKey: 'sidebar.internalAudit', icon: 'M7 3h8l4 4v14H7z M15 3v5h5' },
  { href: '/admin/support', labelKey: 'sidebar.adminSupport', icon: 'M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z' },
  { href: '/pilot/status', labelKey: 'sidebar.pilotStatus', icon: 'M12 8v4l3 3 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' },
];

function NavSection({ title, items, pathname, t }: { title: string; items: NavItem[]; pathname: string; t: (key: string) => string }) {
  return (
    <>
      <div className="sidebarSection">{title}</div>
      {items.map((item) => (
        <a
          key={item.href}
          href={item.href}
          className={`navItem ${pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href)) ? 'active' : ''}`}
        >
          <NavIcon d={item.icon} />
          <span>{t(item.labelKey)}</span>
        </a>
      ))}
    </>
  );
}

export default function Sidebar() {
  const pathname = usePathname() || '/';
  const { t } = useLocale();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    setIsAdmin(!!window.localStorage.getItem('pesaguard.admin_token'));
  }, []);

  return (
    <div className="sidebar">
      <div className="sidebarContent">
        <nav className="sidebarNav">
          <NavSection title={t('sidebar.sectionCore')} items={CORE_NAV} pathname={pathname} t={t} />
          <NavSection title={t('sidebar.sectionPilot')} items={PILOT_NAV} pathname={pathname} t={t} />
          <NavSection title={t('sidebar.sectionMore')} items={MORE_NAV} pathname={pathname} t={t} />
          {isAdmin ? <NavSection title={t('sidebar.sectionAdmin')} items={ADMIN_NAV} pathname={pathname} t={t} /> : null}
        </nav>
      </div>
      <div className="sidebarFooter">
        <div className="statusIndicator">
          <div className="dot"></div>
          <span>{t('sidebar.systemNominal')}</span>
        </div>
      </div>
    </div>
  );
}
