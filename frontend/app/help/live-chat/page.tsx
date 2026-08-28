import { ArrowRight, MessageSquareText, PhoneCall, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpLiveChatPage() {
  return (
    <AccountPageShell
      title="Live chat"
      subtitle="Connect with the support team for fast answers during active operational issues or user access blockers."
      actions={
        <a href="/help/contact-support" className="buttonAccent">
          <PhoneCall size={16} /> Start a request
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Agent availability</h2>
              <p className="muted">Support coverage is designed for business-critical user needs.</p>
            </div>
            <span className="badge">Online</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Queue time</span>
              <strong>2 min</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Coverage</span>
              <strong>24/7</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Priority</span>
              <strong>Escalated</strong>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Before you start</h2>
              <p className="muted">Prepare the essentials so the conversation is efficient and actionable.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><MessageSquareText size={18} /></div>
              <div>
                <p className="infoTitle">Describe the issue</p>
                <p className="muted">Share the account, workflow, and exact failure behavior or message.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Use secure channels</p>
                <p className="muted">Never share recovery codes or passwords in a public or unverified channel.</p>
              </div>
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> Agents can help with access help, workflow questions, and critical account incidents
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
