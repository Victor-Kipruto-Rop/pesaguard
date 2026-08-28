import { Bell, Mail, Smartphone, Volume2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsNotificationSettingsPage() {
  return (
    <AccountPageShell
      title="Notification settings"
      subtitle="Control how your team receives alerts, updates, and operational notices across each communication channel."
      actions={
        <button type="button" className="buttonAccent">
          <Bell size={16} /> Save preferences
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Delivery channels</h2>
              <p className="muted">Choose the channels and priority levels you want to receive.</p>
            </div>
            <span className="badge">Synced</span>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Email notifications</strong>
                <p>Operational summaries and account updates.</p>
              </div>
              <div className="infoIcon accentIcon"><Mail size={16} /></div>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Push alerts</strong>
                <p>Critical alerts for candidate triggers and account events.</p>
              </div>
              <div className="infoIcon brandIcon"><Bell size={16} /></div>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>SMS updates</strong>
                <p>Time-sensitive operational notices for authorized recipients.</p>
              </div>
              <div className="infoIcon successIcon"><Smartphone size={16} /></div>
            </div>
            <div className="toggleRow">
              <div>
                <strong>Daily digest</strong>
                <p>Weekly summary with team and system activities.</p>
              </div>
              <div className="infoIcon"><Volume2 size={16} /></div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Priority preferences</h2>
              <p className="muted">Tune which notification classes are treated as urgent.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/notifications?focus=preferences" />
        </section>
      </div>
    </AccountPageShell>
  );
}
