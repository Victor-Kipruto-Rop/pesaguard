'use client';

import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  return (
    <div className="sidebar">
      <div className="sidebarContent">
        <nav className="sidebarNav">
          <a
            href="/"
            className={`navItem ${isActive('/') ? 'active' : ''}`}
          >
            <span className="icon">📊</span>
            <span>Operations</span>
          </a>
          <a
            href="/insights"
            className={`navItem ${isActive('/insights') ? 'active' : ''}`}
          >
            <span className="icon">📈</span>
            <span>Insights & Analytics</span>
          </a>
          <a
            href="/settings"
            className={`navItem ${isActive('/settings') ? 'active' : ''}`}
          >
            <span className="icon">⚙️</span>
            <span>Settings</span>
          </a>
        </nav>
      </div>
      <div className="sidebarFooter">
        <div className="statusIndicator">
          <div className="dot"></div>
          <span>System nominal</span>
        </div>
      </div>
    </div>
  );
}
