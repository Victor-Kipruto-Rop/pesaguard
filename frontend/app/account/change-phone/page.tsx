import { Phone, MessageCircle, ShieldCheck, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountChangePhonePage() {
  return (
    <AccountPageShell
      title="Change Phone"
      subtitle="Keep your recovery and authentication phone number up to date."
      actions={
        <button type="button" className="buttonGhost">
          <MessageCircle size={16} /> Send code
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Phone number</h2>
              <p className="muted">Update the number used for verification and alerts.</p>
            </div>
            <span className="badge">Verified</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="phone-number">Phone number</label>
              <input id="phone-number" className="textInput" type="tel" defaultValue="+254 712 345 678" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="verification-code">Verification code</label>
              <input id="verification-code" className="textInput" type="text" placeholder="Enter code" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Phone size={16} /> Confirm phone
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Verification</h2>
              <p className="muted">Phone updates include an authorization step for secure access control.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Trusted contact</p>
                <p className="muted">Use a mobile number you control at all times.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Secure signal</p>
                <p className="muted">Verification codes are issued only after confirming your identity.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
