import { ArrowRight, PlayCircle, Rocket, ShieldCheck, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpTutorialsPage() {
  return (
    <AccountPageShell
      title="Tutorials"
      subtitle="Step-by-step walkthroughs to help new users and operators become productive faster."
      actions={
        <a href="/help/videos" className="buttonAccent">
          <PlayCircle size={16} /> Watch videos
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Popular walkthroughs</h2>
              <p className="muted">The most visited beginner and admin tutorials for the product.</p>
            </div>
            <span className="badge">Guided</span>
          </div>

          <div className="optionList">
            <a href="/help/getting-started" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Workspace setup</span>
                <p className="muted">Create your workspace, invite your team, and configure the right roles.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/documentation" className="optionCard">
              <div>
                <span className="optionTitle">Operational workflows</span>
                <p className="muted">Learn how to review transactions, complete reconciliations, and monitor tasks.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/developer/authentication" className="optionCard">
              <div>
                <span className="optionTitle">Secure integration setup</span>
                <p className="muted">Configure authentication and onboarding for client or partner integrations.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>What you’ll learn</h2>
              <p className="muted">Practical knowledge for both admin and engineering workflows.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><Rocket size={18} /></div>
              <div>
                <p className="infoTitle">Fast onboarding</p>
                <p className="muted">Move from account creation to operating the platform without delay.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Secure habits</p>
                <p className="muted">Protect access, verify identities, and follow compliance-ready practices.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Operational confidence</p>
                <p className="muted">Use the platform consistently across payment, account, and reconciliation tasks.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
