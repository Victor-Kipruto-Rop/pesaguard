'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { useLocale } from '../lib/i18n';

function IconBase({ children }: { children: ReactNode }) {
  return (
    <span className="icon" aria-hidden="true">
      {children}
    </span>
  );
}

function OperationsIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19h16" />
        <path d="M7 15v-4" />
        <path d="M12 15V7" />
        <path d="M17 15v-2" />
      </svg>
    </IconBase>
  );
}

function InsightsIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19V9" />
        <path d="M10 19V5" />
        <path d="M16 19v-7" />
        <path d="M22 19H2" />
      </svg>
    </IconBase>
  );
}

function ToolsIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 4l6 6" />
        <path d="M8 20l-4-4 8-8 4 4Z" />
      </svg>
    </IconBase>
  );
}

function StatusIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    </IconBase>
  );
}

function SupportIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20a8 8 0 1 0-8-8v1.5a1.5 1.5 0 0 0 3 0V8a5 5 0 1 1 5 5" />
        <path d="M12 22v-2" />
      </svg>
    </IconBase>
  );
}

function AgreementsIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7 3h8l4 4v14H7z" />
        <path d="M15 3v5h5" />
        <path d="M9 13h6" />
        <path d="M9 17h4" />
      </svg>
    </IconBase>
  );
}

function PoliciesIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3 4 6v6c0 5 3.4 8.2 8 9 4.6-.8 8-4 8-9V6l-8-3Z" />
        <path d="m9.5 12 1.6 1.6 3.4-3.6" />
      </svg>
    </IconBase>
  );
}

function SettingsIcon() {
  return (
    <IconBase>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3v2" />
        <path d="M12 19v2" />
        <path d="M4.2 7.2l1.4 1.4" />
        <path d="M18.4 15.4l1.4 1.4" />
        <path d="M3 12h2" />
        <path d="M19 12h2" />
        <path d="M4.2 16.8l1.4-1.4" />
        <path d="M18.4 8.6l1.4-1.4" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </IconBase>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useLocale();

  const isActive = (path: string) => pathname === path;

  return (
    <div className="sidebar">
      <div className="sidebarContent">
        <nav className="sidebarNav">
          <a href="/" className={`navItem ${isActive('/') ? 'active' : ''}`}>
            <OperationsIcon />
            <span>{t('sidebar.operations')}</span>
          </a>
          <a href="/insights" className={`navItem ${isActive('/insights') ? 'active' : ''}`}>
            <InsightsIcon />
            <span>{t('sidebar.insights')}</span>
          </a>
          <a href="/tools" className={`navItem ${isActive('/tools') ? 'active' : ''}`}>
            <ToolsIcon />
            <span>{t('sidebar.tools')}</span>
          </a>
          <a href="/status" className={`navItem ${isActive('/status') ? 'active' : ''}`}>
            <StatusIcon />
            <span>{t('sidebar.status')}</span>
          </a>
          <a href="/support" className={`navItem ${isActive('/support') ? 'active' : ''}`}>
            <SupportIcon />
            <span>{t('sidebar.support')}</span>
          </a>
          <a href="/agreements" className={`navItem ${isActive('/agreements') ? 'active' : ''}`}>
            <AgreementsIcon />
            <span>{t('sidebar.agreements')}</span>
          </a>
          <a href="/policies" className={`navItem ${isActive('/policies') ? 'active' : ''}`}>
            <PoliciesIcon />
            <span>{t('sidebar.policies')}</span>
          </a>
          <a href="/settings" className={`navItem ${isActive('/settings') ? 'active' : ''}`}>
            <SettingsIcon />
            <span>{t('sidebar.settings')}</span>
          </a>
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
