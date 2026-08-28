'use client';

import { Bell, Mail, Smartphone } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';
import NotificationsList from '../../../../components/notifications/NotificationsList';

export default function NotificationSettingsPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Notification Settings" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Channel controls</h2>
              <p className="muted">Enable or restrict channels at the tenant level.</p>
            </div>
            <span className="badge">Defaults</span>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Email</strong>
                <p>Transactional and operational emails.</p>
              </div>
              <div className="infoIcon accentIcon"><Mail size={16} /></div>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Push</strong>
                <p>Immediate device alerts for critical events.</p>
              </div>
              <div className="infoIcon brandIcon"><Bell size={16} /></div>
            </div>
            <div className="toggleRow">
              <div>
                <strong>SMS</strong>
                <p>Reserved for critical notifications only.</p>
              </div>
              <div className="infoIcon"><Smartphone size={16} /></div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Routing rules</h2>
              <p className="muted">Create rules to route notifications by priority and tenant.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/admin/notifications?focus=routing" />
        </section>
      </div>
    </main>
  );
}
