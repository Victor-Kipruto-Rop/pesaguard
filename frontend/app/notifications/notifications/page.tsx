import { BellRing, CheckCheck, Filter, SlidersHorizontal } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';
import AuthGuard from '../../../components/AuthGuard';

export default function NotificationsNotificationsPage() {
  return (
    <AuthGuard>
      <AccountPageShell
      title="Notifications"
      subtitle="Stay aligned with account activity, security updates, and operational signals across your workspace."
      actions={
        <button type="button" className="buttonGhost">
          <SlidersHorizontal size={16} /> Filter
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Overview</h2>
              <p className="muted">Priority updates requiring attention and review.</p>
            </div>
            <span className="badge">24 unread</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Critical</span>
              <strong>4</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Today</span>
              <strong>12</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Resolved</span>
              <strong>86%</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent activity</h2>
              <p className="muted">The most important events from your team and system environment.</p>
            </div>
          </div>

          <NotificationsList />
        </section>
      </div>
      </AccountPageShell>
    </AuthGuard>
  );
}
