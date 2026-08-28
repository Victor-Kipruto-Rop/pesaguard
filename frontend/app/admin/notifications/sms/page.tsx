'use client';

import { MessageSquareText, Check } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';
import NotificationsList from '../../../../components/notifications/NotificationsList';

export default function SmsPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="SMS" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>SMS channel</h2>
              <p className="muted">Numbers, verification status, and usage metrics.</p>
            </div>
            <span className="badge">Managed</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Verified numbers</span>
              <strong>14</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Sent today</span>
              <strong>28</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Audit</h2>
              <p className="muted">Delivery and compliance history for SMS messages.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/admin/notifications?channel=sms" />
        </section>
      </div>
    </main>
  );
}
