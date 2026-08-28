import { Key, PlusCircle, ShieldCheck, Zap, Clock3 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountApiTokensPage() {
  return (
    <AccountPageShell
      title="API Tokens"
      subtitle="Manage service credentials for integrations and automation without exposing secret data."
      actions={
        <button type="button" className="buttonAccent">
          <PlusCircle size={16} /> Create token
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Token controls</h2>
              <p className="muted">A premium token workspace for secure automation keys.</p>
            </div>
            <span className="badge">Protected</span>
          </div>

          <div className="listCardPanel">
            <div className="listCardItem">
              <div className="listCardIcon brandIcon"><Key size={18} /></div>
              <div className="listCardText">
                <strong>ops-integration-prod</strong>
                <span>Used for reconciliation sync • Expires in 90 days</span>
              </div>
              <span className="statusPill success">Active</span>
            </div>

            <div className="listCardItem">
              <div className="listCardIcon accentIcon"><Clock3 size={18} /></div>
              <div className="listCardText">
                <strong>support-reader-token</strong>
                <span>Read-only access • Last rotated 3 weeks ago</span>
              </div>
              <span className="statusPill">Review</span>
            </div>

            <div className="listCardItem mutedItem">
              <div className="listCardIcon brandIcon"><Key size={18} /></div>
              <div className="listCardText">
                <strong>legacy-audit-token</strong>
                <span>Deprecated and scheduled for removal</span>
              </div>
              <button type="button" className="inlineAction">Revoke</button>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Secure integration</h2>
              <p className="muted">Only deploy tokens with the correct permissions and expiry configuration.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Scoped access</p>
                <p className="muted">Limit tokens to the exact endpoints and roles needed.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Zap size={18} /></div>
              <div>
                <p className="infoTitle">Safe rotation</p>
                <p className="muted">Rotate keys regularly and revoke unused credentials quickly.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
