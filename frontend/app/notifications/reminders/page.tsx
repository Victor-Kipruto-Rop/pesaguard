import { Clock3, ListTodo, Repeat2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsRemindersPage() {
  return (
    <AccountPageShell
      title="Reminders"
      subtitle="Manage time-based nudges, scheduled follow-ups, and recurring operational check-ins."
      actions={
        <button type="button" className="buttonAccent">
          <Repeat2 size={16} /> New reminder
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Upcoming reminders</h2>
              <p className="muted">Actions and follow-ups scheduled to keep your team on track.</p>
            </div>
            <span className="badge">5 due soon</span>
          </div>

          <NotificationsList apiPath="/api/notifications?type=reminder" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Smart scheduling</h2>
              <p className="muted">Reminders are aligned with business windows and operational priorities.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ListTodo size={18} /></div>
              <div>
                <p className="infoTitle">Task recurrence</p>
                <p className="muted">Set recurring reminders for weekly reviews, reconciliations, and support triage.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Clock3 size={18} /></div>
              <div>
                <p className="infoTitle">Adaptive timing</p>
                <p className="muted">Deliver reminders at times when teams are most likely to respond to urgent work.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
