import { ArrowRight, FileText, History, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpTicketHistoryPage() {
  return (
    <AccountPageShell
      title="Ticket history"
      subtitle="Review your recent support cases, resolutions, and patterns from prior operational issues."
      actions={
        <a href="/help/create-ticket" className="buttonAccent">
          <FileText size={16} /> New ticket
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent cases</h2>
              <p className="muted">Your recent support interactions with their current resolution state.</p>
            </div>
            <span className="badge">3 active</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><History size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>#PSG-10482</strong>
                  <span className="statusPill success">Resolved</span>
                </div>
                <p>Payment reconciliation delay on settlement batch updates.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><History size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>#PSG-10211</strong>
                  <span className="statusPill">Escalated</span>
                </div>
                <p>Access review for a role-based permission mismatch.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><History size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>#PSG-10083</strong>
                  <span className="statusPill success">Closed</span>
                </div>
                <p>Webhook retry issue caused by signature validation mismatch.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Ticket lifecycle</h2>
              <p className="muted">How support requests move from intake to resolution.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Open and route</p>
                <p className="muted">Tickets are triaged based on urgency, impact, and operational area.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ArrowRight size={18} /></div>
              <div>
                <p className="infoTitle">Investigate and resolve</p>
                <p className="muted">The support team updates the case with findings and any action taken.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
