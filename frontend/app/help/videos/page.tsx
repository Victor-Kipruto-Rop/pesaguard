import { ArrowRight, PlayCircle, Rocket, Video } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpVideosPage() {
  return (
    <AccountPageShell
      title="Videos"
      subtitle="Watch short walkthroughs for onboarding, platform tasks, and integration how-to sessions."
      actions={
        <a href="/help/tutorials" className="buttonAccent">
          <PlayCircle size={16} /> Browse tutorials
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Featured sessions</h2>
              <p className="muted">Short-form content covering common day-to-day user and admin actions.</p>
            </div>
            <span className="badge">Fresh</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><Video size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>First-time workspace setup</strong>
                  <span className="statusPill success">6 min</span>
                </div>
                <p>Walk through account creation, security checks, and tenant access setup.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Video size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Reconciliation overview</strong>
                  <span className="statusPill">8 min</span>
                </div>
                <p>Understand how payout events, exceptions, and approvals fit together.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><Rocket size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>API onboarding</strong>
                  <span className="statusPill success">10 min</span>
                </div>
                <p>Learn the fundamentals of client authentication, callback setup, and safe testing.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Learning path</h2>
              <p className="muted">Move from setup to advanced operational confidence.</p>
            </div>
          </div>

          <div className="optionList">
            <a href="/help/getting-started" className="optionCard">
              <div>
                <span className="optionTitle">Start here</span>
                <p className="muted">Set up the account and workspace correctly before moving into deeper workflows.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/api-guides" className="optionCard">
              <div>
                <span className="optionTitle">Developer content</span>
                <p className="muted">Move into secure API patterns and integration design with more detailed references.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
