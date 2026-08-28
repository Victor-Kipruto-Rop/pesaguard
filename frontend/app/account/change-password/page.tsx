import { Lock, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountChangePasswordPage() {
  return (
    <AccountPageShell
      title="Change Password"
      subtitle="Set a strong password and reduce exposure for sensitive account actions."
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Password controls</h2>
              <p className="muted">Use multi-layer protection for your PesaGuard login.</p>
            </div>
            <span className="badge">Strong</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="current-password">Current password</label>
              <input id="current-password" className="textInput" type="password" placeholder="••••••••" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="new-password">New password</label>
              <input id="new-password" className="textInput" type="password" placeholder="Enter a new secure password" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="confirm-password">Confirm password</label>
              <input id="confirm-password" className="textInput" type="password" placeholder="Repeat new password" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Lock size={16} /> Save password
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Password health</h2>
              <p className="muted">Passwords should be unique, long, and easy to manage with a password vault.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Prefer phrases over simple words.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Rotate passwords after major access changes.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Use multi-factor authentication whenever possible.</span>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Security posture</p>
                <p className="muted">Your current settings already meet the recommended security baseline.</p>
              </div>
            </div>
          </div>

          <div className="featureBadge">
            <Sparkles size={16} /> Strong password recommended
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
