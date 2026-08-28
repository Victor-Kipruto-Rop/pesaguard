import { AlertTriangle, Bell, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsAlertsPage() {
  return (
    <AccountPageShell
      title="Alerts"
      subtitle="Monitor critical issues, risk indicators, and urgent operational changes in one place."
      actions={
        <button type="button" className="buttonGhost">
          <ShieldCheck size={16} /> Review escalation
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Active alerts</h2>
              <p className="muted">Priority issues needing immediate attention or investigation.</p>
            </div>
            <span className="badge">3 critical</span>
          </div>

          <NotificationsList apiPath="/api/notifications?type=alert" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Escalation status</h2>
              <p className="muted">Current prioritization and the next recommended action for the team.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Delay investigation</strong>
                <p>Ops team is validating whether the queue has been affected by a recent batch merge.</p>
              </div>
              <span className="statusPill warning">Critical</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Access review</strong>
                <p>Security review on the login attempt is complete and the account remains protected.</p>
              </div>
              <span className="statusPill success">Resolved</span>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
