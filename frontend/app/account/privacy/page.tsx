import { ShieldCheck, EyeOff, Lock, Key, BellRing } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountPrivacyPage() {
  return (
    <AccountPageShell
      title="Privacy"
      subtitle="Configure how sensitive account data is displayed and shared within PesaGuard."
      actions={
        <button type="button" className="buttonGhost">
          <EyeOff size={16} /> Privacy audit
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Data visibility</h2>
              <p className="muted">Adjust visibility of sensitive account details across sessions.</p>
            </div>
            <span className="badge">Restricted</span>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Protected information</strong>
                <p className="muted">Show only the minimum details needed for daily operations.</p>
              </div>
              <span className="toggleSwitch" />
            </div>

            <div className="toggleRow active">
              <div>
                <strong>Secure exchange</strong>
                <p className="muted">Keep audit records privacy-safe with masked metadata by default.</p>
              </div>
              <span className="toggleSwitch" />
            </div>

            <div className="toggleRow">
              <div>
                <strong>Public profile visibility</strong>
                <p className="muted">Display limited contact profile details outside the workspace.</p>
              </div>
              <span className="toggleSwitch" />
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Control panel</h2>
              <p className="muted">Privacy defaults are a core part of PesaGuard’s security posture.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><EyeOff size={18} /></div>
              <div>
                <p className="infoTitle">Limit screen sharing</p>
                <p className="muted">Reduce visible details during operational reviews and support sessions.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Lock size={18} /></div>
              <div>
                <p className="infoTitle">Data protection</p>
                <p className="muted">Keep sensitive logs and tokens hidden from broader access groups.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><BellRing size={18} /></div>
              <div>
                <p className="infoTitle">Alert hygiene</p>
                <p className="muted">Only high-trust alert notifications are surfaced for privacy-sensitive events.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
