'use client';

import { SlidersHorizontal, Bell, CheckCheck } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';
import NotificationsList from '../../../../components/notifications/NotificationsList';
import AuthGuard from '../../../../components/AuthGuard';

export default function NotificationsPage() {
  return (
    <AuthGuard>
      <main className="shell">
        <PageHeader eyebrow="Admin" title="Notifications" summary="Tenant administration view for this module." />

        <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Tenant overview</h2>
              <p className="muted">Review cross-tenant notification volumes and priority routing.</p>
            </div>
            <div>
              <button className="buttonGhost"><SlidersHorizontal size={14} /> Filters</button>
            </div>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Total sent</span>
              <strong>12,482</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Failed</span>
              <strong>24</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Avg delivery</span>
              <strong>1.2s</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent events</h2>
              <p className="muted">Latest notification activity across tenants and channels.</p>
            </div>
          </div>

          <NotificationsList apiBase={process.env.NEXT_PUBLIC_API_BASE_URL} />
        </section>
        </div>
      </main>
    </AuthGuard>
  );
}
