import { BellRing, Smartphone, Zap } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsPushPage() {
  return (
    <AccountPageShell
      title="Push notifications"
      subtitle="Stay instant with critical account, system, and workflow updates delivered to your active devices."
      actions={
        <button type="button" className="buttonAccent">
          <BellRing size={16} /> Manage devices
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Device delivery</h2>
              <p className="muted">Push alerts are routed to your current active devices and session endpoints.</p>
            </div>
            <span className="badge">3 connected</span>
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
            <div className="statusTile">
              <span className="statusLabel">Desktop</span>
              <strong>Ready</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Alert priority</h2>
              <p className="muted">Only the most relevant operational and security events are sent immediately to push channels.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/notifications?channel=push" />
        </section>
      </div>
    </AccountPageShell>
  );
}
