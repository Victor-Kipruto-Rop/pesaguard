import { ArrowRight, BadgeAlert, FileText, Radar, Send } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpCreateTicketPage() {
  return (
    <AccountPageShell
      title="Create a support ticket"
      subtitle="Submit a precise incident report so the support team can triage the right priority and fastest resolution path."
      actions={
        <a href="/help/ticket-history" className="buttonGhost">
          <FileText size={16} /> View ticket history
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Ticket details</h2>
              <p className="muted">Share key facts to speed up diagnosis and resolution.</p>
            </div>
            <span className="badge">New case</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="ticket-title">Summary</label>
              <input id="ticket-title" className="textInput" type="text" defaultValue="Payment reconciliation delay affecting ledger updates" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="ticket-priority">Priority</label>
              <select id="ticket-priority" className="selectInput" defaultValue="high">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div className="fieldGroup">
              <label htmlFor="ticket-impact">Impact</label>
              <input id="ticket-impact" className="textInput" type="text" defaultValue="Affects 3 merchant settlements and delays reconciliations" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="ticket-description">Description</label>
              <textarea id="ticket-description" className="textInput" rows={6} defaultValue="Transactions completed successfully but the settlement queue is delayed by 18 minutes. The mismatch is visible in reconciliation records and appears after the payment confirmation event." />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Send size={16} /> Submit ticket
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Case guidance</h2>
              <p className="muted">Include the details the support team needs to move quickly.</p>
            </div>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><BadgeAlert size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>What to add</strong>
                  <span className="statusPill success">Required</span>
                </div>
                <p>Incident timestamps, affected IDs, impacted workflows, and screenshot evidence.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Radar size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Best practice</strong>
                  <span className="statusPill">Faster triage</span>
                </div>
                <p>Call out whether this is a security issue, user access issue, or operational delay.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
