import { Megaphone, Sparkles, TrendingUp } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsAnnouncementsPage() {
  return (
    <AccountPageShell
      title="Announcements"
      subtitle="Keep your team informed on product improvements, policy updates, and important operational milestones."
      actions={
        <button type="button" className="buttonAccent">
          <Megaphone size={16} /> View all
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Latest updates</h2>
              <p className="muted">Announcements that affect workflow, policy, or product experience.</p>
            </div>
            <span className="badge">2 new</span>
          </div>

          <NotificationsList apiPath="/api/notifications?type=announcement" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>What matters</h2>
              <p className="muted">The announcements currently relevant to your team and business context.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><Megaphone size={18} /></div>
              <div>
                <p className="infoTitle">Operational reliability</p>
                <p className="muted">Planned reliability upgrades and automation improvements are shared here.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><TrendingUp size={18} /></div>
              <div>
                <p className="infoTitle">Platform improvements</p>
                <p className="muted">New productivity features and workflow enhancements are announced as they ship.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
