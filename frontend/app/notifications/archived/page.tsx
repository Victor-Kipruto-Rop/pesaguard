import { Archive, FolderOpenDot, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsArchivedPage() {
  return (
    <AccountPageShell
      title="Archived"
      subtitle="Review previously cleared alerts, resolved issues, and older team updates saved for historical context."
      actions={
        <button type="button" className="buttonGhost">
          <Archive size={16} /> Restore items
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Recently archived</h2>
              <p className="muted">Closed incidents and resolved messages kept for reference.</p>
            </div>
            <span className="badge">128 items</span>
          </div>

          <NotificationsList apiPath="/api/notifications?filter=archived" />
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Retention note</h2>
              <p className="muted">Archived items stay available for operational and compliance review.</p>
            </div>
          </div>

          <div className="featureBadge">
            <Archive size={16} /> Archived content is retained according to your workspace retention and compliance rules
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
