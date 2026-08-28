import { Mail, Send, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsEmailsPage() {
  return (
    <AccountPageShell
      title="Email"
      subtitle="Review email alerts, summaries, and account-specific operational messages with context."
      actions={
        <button type="button" className="buttonAccent">
          <Send size={16} /> Send update
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent mail</h2>
              <p className="muted">System-generated emails, summaries, and important account notifications.</p>
            </div>
            <span className="badge">12 unread</span>
          </div>

          <NotificationsList apiPath="/api/notifications?channel=email" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Email flow</h2>
              <p className="muted">Operational emails are routed based on urgency and account activity.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Priority alerts</p>
                <p className="muted">Critical events are delivered immediately with the relevant context attached.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Mail size={18} /></div>
              <div>
                <p className="infoTitle">Digest summaries</p>
                <p className="muted">Lower urgency messages are bundled and sent at scheduled intervals.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
