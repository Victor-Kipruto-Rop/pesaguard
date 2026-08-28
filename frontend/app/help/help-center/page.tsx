import { ArrowRight, BookOpenText, LifeBuoy, Search, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpHelpCenterPage() {
  return (
    <AccountPageShell
      title="Help center"
      subtitle="Find the right answer quickly with guided support, onboarding content, and operational troubleshooting."
      actions={
        <a href="/help/contact-support" className="buttonAccent">
          <LifeBuoy size={16} /> Contact support
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Popular topics</h2>
              <p className="muted">Most used guidance for secure onboarding and day-to-day operations.</p>
            </div>
            <span className="badge">Featured</span>
          </div>

          <div className="optionList">
            <a href="/help/getting-started" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Getting started</span>
                <p className="muted">Set up your account, permissions, and workspace correctly.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/troubleshooting" className="optionCard">
              <div>
                <span className="optionTitle">Troubleshooting</span>
                <p className="muted">Diagnose failed transactions, sync delays, and access issues.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/help/documentation" className="optionCard">
              <div>
                <span className="optionTitle">Documentation</span>
                <p className="muted">Reference installation, API, and operational instructions.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Quick answers</h2>
              <p className="muted">Self-serve support for common product and security questions.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Search size={18} /></div>
              <div>
                <p className="infoTitle">Can I reset my access without admin help?</p>
                <p className="muted">Yes. Use the password recovery or MFA reset flows in your secure account pathways.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><BookOpenText size={18} /></div>
              <div>
                <p className="infoTitle">Where do I learn the integration model?</p>
                <p className="muted">Review the API guides, examples, and Postman collection for implementation guidance.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">How do I report a security issue?</p>
                <p className="muted">Use the support request flow and mark the issue as high priority for security review.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
