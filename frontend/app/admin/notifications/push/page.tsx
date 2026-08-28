'use client';

import { Smartphone, Zap } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';
import NotificationsList from '../../../../components/notifications/NotificationsList';

export default function PushPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Push" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Push channels</h2>
              <p className="muted">Connected device endpoints and delivery metrics.</p>
            </div>
            <span className="badge">3 devices</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Web</span>
              <strong>Enabled</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Mobile</span>
              <strong>Active</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Priority rules</h2>
              <p className="muted">Which events are promoted to immediate push delivery.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/admin/notifications?channel=push" />
        </section>
      </div>
    </main>
  );
}
