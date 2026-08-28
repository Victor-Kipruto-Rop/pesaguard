import { ArrowRight, Users, MessageSquareText, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpCommunityPage() {
  return (
    <AccountPageShell
      title="Community"
      subtitle="Connect with peers, learn from shared experiences, and stay close to product changes and operational best practices."
      actions={
        <a href="/help/feedback" className="buttonAccent">
          <Users size={16} /> Share feedback
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Community highlights</h2>
              <p className="muted">Topics and discussions designed to help teams move faster with confidence.</p>
            </div>
            <span className="badge">Active</span>
          </div>

          <div className="optionList">
            <a href="/help/tutorials" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Operational playbooks</span>
                <p className="muted">Shared patterns for onboarding, account handling, and support efficiency.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/feedback" className="optionCard">
              <div>
                <span className="optionTitle">Product discussions</span>
                <p className="muted">Review new improvements, suggestions, and product updates from active users.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Community signals</h2>
              <p className="muted">Popular topics and team conversations around the platform.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Users size={18} /></div>
              <div>
                <p className="infoTitle">Team onboarding</p>
                <p className="muted">How operations teams set up secure roles and access quickly.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><MessageSquareText size={18} /></div>
              <div>
                <p className="infoTitle">Support efficiency</p>
                <p className="muted">Best practices for ticket triage, escalation, and faster issue resolution.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Product updates</p>
                <p className="muted">Track release notes, new workflows, and product milestones from the wider community.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
