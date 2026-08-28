import { ArrowRight, FileText, MessageSquareText, ShieldCheck, TimerReset } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpTicketDetailsPage() {
  return (
    <AccountPageShell
      title="Ticket details"
      subtitle="Follow the status, ownership, and communication trail for an active support request."
      actions={
        <a href="/help/ticket-history" className="buttonGhost">
          <FileText size={16} /> All tickets
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>#PSG-10482</h2>
              <p className="muted">Payment reconciliation delay affecting ledger updates.</p>
            </div>
            <span className="badge">In progress</span>
          </div>

          <div className="miniStatGrid">
            <div className="miniStat">
              <span>Priority</span>
              <strong>High</strong>
            </div>
            <div className="miniStat">
              <span>Status</span>
              <strong>Escalated</strong>
            </div>
            <div className="miniStat">
              <span>Owner</span>
              <strong>Ops team</strong>
            </div>
            <div className="miniStat">
              <span>Updated</span>
              <strong>12 min ago</strong>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><TimerReset size={18} /></div>
              <div>
                <p className="infoTitle">Latest update</p>
                <p className="muted">Support has confirmed the delay is tied to an upstream reconciliation queue and is actively investigating.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><MessageSquareText size={18} /></div>
              <div>
                <p className="infoTitle">Conversation trail</p>
                <p className="muted">The team requested timestamps and affected transaction IDs to narrow the issue to a recent batch.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Case notes</h2>
              <p className="muted">Actionable operational detail captured for the team.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Queue review started</strong>
                <p>Support reviewed recent ledger and settlement batches.</p>
              </div>
              <span className="statusPill success">Complete</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Escalation sent</strong>
                <p>Ops team requested a deeper check against the reconciliation engine.</p>
              </div>
              <span className="statusPill success">Complete</span>
            </div>
            <div className="toggleRow">
              <div>
                <strong>Awaiting confirmation</strong>
                <p>Waiting on the next system response to confirm the fix window.</p>
              </div>
              <span className="statusPill">Pending</span>
            </div>
          </div>

          <div className="featureBadge">
            <ShieldCheck size={16} /> Sensitive update details remain restricted to the support and ops team
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
