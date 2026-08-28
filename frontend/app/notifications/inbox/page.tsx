import { Inbox, MessageSquareText, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsInboxPage() {
  return (
    <AccountPageShell
      title="Inbox"
      subtitle="Review the latest messages, updates, and operational notes from your workspace."
      actions={
        <button type="button" className="buttonAccent">
          <Inbox size={16} /> Mark all read
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Priority threads</h2>
              <p className="muted">Open conversations that need research, follow-up, or action.</p>
            </div>
            <span className="badge">7 active</span>
          </div>

          <NotificationsList apiPath="/api/notifications?inbox=true" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Message center</h2>
              <p className="muted">Structured updates and the most recent operational context.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">New workflow release</p>
                <p className="muted">A new settlement overview is now available in the operational dashboard.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><MessageSquareText size={18} /></div>
              <div>
                <p className="infoTitle">Team comment received</p>
                <p className="muted">A team member left a follow-up on the ledger mismatch and flagged the exception for review.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
