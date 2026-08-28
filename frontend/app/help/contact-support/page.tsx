import { ArrowRight, Headphones, Mail, MessageSquareMore, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpContactSupportPage() {
  return (
    <AccountPageShell
      title="Contact support"
      subtitle="Reach the right team quickly for operational incidents, account help, and secure escalation requests."
      actions={
        <a href="/help/create-ticket" className="buttonAccent">
          <Headphones size={16} /> Create ticket
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Send a request</h2>
              <p className="muted">Tell us what’s happening and the support team will route it correctly.</p>
            </div>
            <span className="badge">Priority routing</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="support-name">Full name</label>
              <input id="support-name" className="textInput" type="text" defaultValue="Victor Kipruto" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="support-email">Work email</label>
              <input id="support-email" className="textInput" type="email" defaultValue="victor@pesaguard.co" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="support-topic">Issue type</label>
              <select id="support-topic" className="selectInput" defaultValue="account-access">
                <option value="account-access">Account access</option>
                <option value="payment-issue">Payment issue</option>
                <option value="security">Security concern</option>
                <option value="technical">Technical support</option>
              </select>
            </div>
            <div className="fieldGroup">
              <label htmlFor="support-message">Message</label>
              <textarea id="support-message" className="textInput" rows={5} defaultValue="We are seeing repeated authentication attempts and need a secure review of the account access flow." />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Mail size={16} /> Submit request
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Support channels</h2>
              <p className="muted">Choose the fastest path based on urgency and account impact.</p>
            </div>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><MessageSquareMore size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Live chat</strong>
                  <span className="statusPill success">Online</span>
                </div>
                <p>Available for immediate questions and guided troubleshooting.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><ShieldCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Security escalation</strong>
                  <span className="statusPill">High priority</span>
                </div>
                <p>For account compromise, suspicious access, or abnormal payment activity.</p>
              </div>
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> Response targets vary by priority, but standard tickets are triaged within business hours
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
