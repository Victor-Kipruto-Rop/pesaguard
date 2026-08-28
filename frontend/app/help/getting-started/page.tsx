import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles, UserPlus } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpGettingStartedPage() {
  return (
    <AccountPageShell
      title="Getting started"
      subtitle="Set up your workspace with the right mix of account access, security, and operational visibility."
      actions={
        <a href="/auth/register" className="buttonAccent">
          <UserPlus size={16} /> Create account
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Setup checklist</h2>
              <p className="muted">A simple sequence to get your team secure and operational.</p>
            </div>
            <span className="badge">Onboarding</span>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>1. Confirm your account</strong>
                <p>Verify your contact details and complete secure sign-in setup.</p>
              </div>
              <span className="statusPill success">Ready</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>2. Configure MFA</strong>
                <p>Set up authenticator or recovery methods for account protection.</p>
              </div>
              <span className="statusPill success">Ready</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>3. Review workspace permissions</strong>
                <p>Ensure the correct team, role, and access rights are assigned.</p>
              </div>
              <span className="statusPill success">Ready</span>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recommended next steps</h2>
              <p className="muted">Move from setup into real operational usage quickly.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Connect your team</p>
                <p className="muted">Add collaborators and assign appropriate operational roles.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Finalize secure access</p>
                <p className="muted">Confirm recovery methods and alert preferences before live activity.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Start with your first workflow</p>
                <p className="muted">Use the dashboard, transactions, and reports to begin meaningful work.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
