import { MessageSquareText, Smartphone, Check } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';
import NotificationsList from '../../../components/notifications/NotificationsList';

export default function NotificationsSmsPage() {
  return (
    <AccountPageShell
      title="SMS"
      subtitle="Manage secure text alerts for high-priority access and operational events that require quick action."
      actions={
        <button type="button" className="buttonAccent">
          <Check size={16} /> Verify number
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Active SMS channel</h2>
              <p className="muted">High-priority updates are sent to verified mobile numbers only.</p>
            </div>
            <span className="badge">Verified</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Number</span>
              <strong>+254 712 555 482</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Status</span>
              <strong>On</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Priority</span>
              <strong>Critical</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Text alert policy</h2>
              <p className="muted">SMS is reserved for the most urgent and time-sensitive operational issues.</p>
            </div>
          </div>

          <NotificationsList apiPath="/api/notifications?channel=sms" />
        </section>
      </div>
    </AccountPageShell>
  );
}
