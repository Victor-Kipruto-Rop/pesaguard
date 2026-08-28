'use client';

import { Mail, FileText } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';
import NotificationsList from '../../../../components/notifications/NotificationsList';

export default function EmailPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Email" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Delivery health</h2>
              <p className="muted">Track email deliverability, bounces, and reputation metrics.</p>
            </div>
            <span className="badge">Healthy</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Sent today</span>
              <strong>8,342</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Bounce rate</span>
              <strong>0.3%</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Templates</h2>
              <p className="muted">Manage tenant email templates and preview content.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/admin/notifications?channel=email" />
        </section>
      </div>
    </main>
  );
}
