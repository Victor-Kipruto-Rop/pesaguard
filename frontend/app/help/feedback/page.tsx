import { ArrowRight, MessageSquareQuote, Rocket, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpFeedbackPage() {
  return (
    <AccountPageShell
      title="Feedback"
      subtitle="Share product feedback, gaps, and ideas to help the platform evolve around real operations."
      actions={
        <a href="/help/community" className="buttonAccent">
          <MessageSquareQuote size={16} /> Join community
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Share your input</h2>
              <p className="muted">We use operational feedback to improve dashboards, workflows, and support journeys.</p>
            </div>
            <span className="badge">Ideas</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="feedback-area">Area</label>
              <select id="feedback-area" className="selectInput" defaultValue="dashboard">
                <option value="dashboard">Dashboard experience</option>
                <option value="support">Support flow</option>
                <option value="security">Security and access</option>
                <option value="integration">Integrations</option>
              </select>
            </div>
            <div className="fieldGroup">
              <label htmlFor="feedback-summary">Summary</label>
              <input id="feedback-summary" className="textInput" type="text" defaultValue="Need better reconciliation drill-down on exception pages" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="feedback-detail">Details</label>
              <textarea id="feedback-detail" className="textInput" rows={6} defaultValue="The exception workflow is generally clear, but more context around root-cause tags would help our support and operations teams act faster." />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <Rocket size={16} /> Submit feedback
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Why this matters</h2>
              <p className="muted">Product feedback directly informs the product experience and roadmap.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Operational insight</p>
                <p className="muted">Real user pain points guide new design and workflow improvements.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><MessageSquareQuote size={18} /></div>
              <div>
                <p className="infoTitle">Faster product iteration</p>
                <p className="muted">Feedback funnels into product changes with clearer release prioritization.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
