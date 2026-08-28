import { AlertTriangle, ShieldCheck, Trash2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountDeleteAccountPage() {
  return (
    <AccountPageShell
      title="Delete Account"
      subtitle="This is a sensitive security action. Only proceed if you fully understand the impact."
    >
      <div className="panelGrid">
        <section className="sectionPanel dangerPanel">
          <div className="panelHeader">
            <div>
              <h2>Account removal</h2>
              <p className="muted">Deleting your account removes access and clears personal settings.</p>
            </div>
            <span className="badge dangerBadge">Danger</span>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <span className="infoBullet dangerBullet" />
              <span className="muted">Data associated with this account may no longer be recoverable.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet dangerBullet" />
              <span className="muted">This action requires verification from the account owner.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet dangerBullet" />
              <span className="muted">This will remove linked access and invalidate active trust tokens.</span>
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonDanger">
              <Trash2 size={16} /> Delete account
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Safety checklist</h2>
              <p className="muted">Review the risks before you remove access to your account.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Confirm you have exported any audit reports or historical exports you need.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Check that no critical workflows depend on this account or linked access.</span>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Confirmation required</p>
                <p className="muted">Account deletion is protected by a final verification step and admin review.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
