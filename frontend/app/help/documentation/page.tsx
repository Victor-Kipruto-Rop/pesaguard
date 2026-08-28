import { ArrowRight, BookOpenText, FileText, ShieldCheck, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpDocumentationPage() {
  return (
    <AccountPageShell
      title="Documentation"
      subtitle="Browse the operational reference library covering onboarding, integrations, security, and platform behavior."
      actions={
        <a href="/help/api-guides" className="buttonAccent">
          <BookOpenText size={16} /> Browse guides
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Core documentation</h2>
              <p className="muted">Reference material for administrators, developers, and operations teams.</p>
            </div>
            <span className="badge">Updated</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><FileText size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Platform overview</strong>
                  <span className="statusPill success">Core</span>
                </div>
                <p>System architecture, roles, trust boundaries, and operational responsibilities.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><ShieldCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Security policies</strong>
                  <span className="statusPill">Protected</span>
                </div>
                <p>Access controls, password standards, MFA, and audit expectations.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><Sparkles size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Ops playbooks</strong>
                  <span className="statusPill success">Live</span>
                </div>
                <p>Troubleshooting steps, escalation flows, and routine checks.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recommended reads</h2>
              <p className="muted">Start here based on what you need to do next.</p>
            </div>
          </div>

          <div className="optionList">
            <a href="/help/getting-started" className="optionCard">
              <div>
                <span className="optionTitle">Getting started</span>
                <p className="muted">New-user onboarding and first configuration steps.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/tutorials" className="optionCard">
              <div>
                <span className="optionTitle">Tutorials</span>
                <p className="muted">Hands-on walkthroughs for application setup and daily use.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
