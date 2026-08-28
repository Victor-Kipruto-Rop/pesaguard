import { User, Edit3, Mail, Globe } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountEditProfilePage() {
  return (
    <AccountPageShell
      title="Edit Profile"
      subtitle="Adjust your account identity, display name, and contact preferences."
      actions={
        <button type="button" className="buttonGhost">
          <Edit3 size={16} /> Edit details
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Profile settings</h2>
              <p className="muted">Choose how your account appears across the PesaGuard console.</p>
            </div>
          </div>
          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="display-name">Display name</label>
              <input id="display-name" className="textInput" type="text" placeholder="Example: Security Admin" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="job-title">Job title</label>
              <input id="job-title" className="textInput" type="text" placeholder="Example: Operations Lead" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="website">Website</label>
              <input id="website" className="textInput" type="url" placeholder="https://" />
            </div>
          </div>
          <div className="formActions">
            <button type="button" className="buttonAccent">
              <User size={16} /> Save profile
            </button>
          </div>
        </section>
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Professional identity</h2>
              <p className="muted">A polished profile improves collaboration across security and finance teams.</p>
            </div>
          </div>
          <div className="infoList">
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Keep your title aligned with your organization’s role structure.</span>
            </div>
            <div className="infoRow">
              <span className="infoBullet" />
              <span className="muted">Use a professional username for audit and session references.</span>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
