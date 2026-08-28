import { User, Briefcase, Mail, Globe, ShieldCheck, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountProfilePage() {
  return (
    <AccountPageShell
      title="Profile"
      subtitle="Review your account identity and security profile settings."
      actions={
        <button type="button" className="buttonGhost">
          <User size={16} /> View profile
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Personal profile</h2>
              <p className="muted">Keep your account details aligned with your organizational role.</p>
            </div>
            <span className="badge">Verified</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="name">Full name</label>
              <input id="name" className="textInput" type="text" defaultValue="Victor Kipruto" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="email">Work email</label>
              <input id="email" className="textInput" type="email" defaultValue="victor@pesaguard.co" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="role">Role</label>
              <input id="role" className="textInput" type="text" defaultValue="Operations Director" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Mail size={16} /> Save changes
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Professional identity</h2>
              <p className="muted">The point of contact for investigation, escalation, and support workflows.</p>
            </div>
          </div>

          <div className="miniStatGrid">
            <div className="miniStat">
              <span>Role visibility</span>
              <strong>Operations</strong>
            </div>
            <div className="miniStat">
              <span>Last review</span>
              <strong>14 Jul</strong>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Briefcase size={18} /></div>
              <div>
                <p className="infoTitle">Role visibility</p>
                <p className="muted">Ensure your role label is accurate for audit trails and team approvals.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Globe size={18} /></div>
              <div>
                <p className="infoTitle">External contact</p>
                <p className="muted">Use a monitored address for security notifications and operational escalations.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Trust status</p>
                <p className="muted">Identity checks are current and aligned with your organization’s access policy.</p>
              </div>
            </div>
          </div>

          <div className="featureBadge">
            <Sparkles size={16} /> Identity is aligned with company policy
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
