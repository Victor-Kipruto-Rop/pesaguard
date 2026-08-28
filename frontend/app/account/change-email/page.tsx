import { Mail, ShieldCheck, RefreshCw, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountChangeEmailPage() {
  return (
    <AccountPageShell
      title="Change Email"
      subtitle="Update the email address associated with your PesaGuard account."
      actions={
        <button type="button" className="buttonGhost">
          <RefreshCw size={16} /> Verify
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Contact email</h2>
              <p className="muted">Set a verified email for security alerts and account recovery.</p>
            </div>
            <span className="badge">Protected</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="current-email">Current email</label>
              <input id="current-email" className="textInput" type="email" defaultValue="victor@pesaguard.co" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="new-email">New email address</label>
              <input id="new-email" className="textInput" type="email" placeholder="new@company.com" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="confirm-email">Confirm new email</label>
              <input id="confirm-email" className="textInput" type="email" placeholder="new@company.com" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Mail size={16} /> Send verification
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Verification safety</h2>
              <p className="muted">Email changes are protected by additional checks to keep your account secure.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Confirm with your current account</p>
                <p className="muted">We never update an address without a verification step.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Delivery assurance</p>
                <p className="muted">A confirmation link is sent to the new address before any change is finalized.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
