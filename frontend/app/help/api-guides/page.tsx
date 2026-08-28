import { ArrowRight, BookOpenText, Code2, FileJson2, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpApiGuidesPage() {
  return (
    <AccountPageShell
      title="API guides"
      subtitle="Detailed reference for secure authentication, request patterns, and production-ready integration flows."
      actions={
        <a href="/developer/api-reference" className="buttonAccent">
          <Code2 size={16} /> Open API docs
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Guides</h2>
              <p className="muted">Implementation help grouped by integration need and platform responsibility.</p>
            </div>
            <span className="badge">Live</span>
          </div>

          <div className="optionList">
            <a href="/developer/authentication" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Authentication</span>
                <p className="muted">Token setup, OAuth scopes, key rotation, and secure identity management.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/developer/callback-guide" className="optionCard">
              <div>
                <span className="optionTitle">Callback guide</span>
                <p className="muted">Signature validation, retry logic, and event processing best practices.</p>
              </div>
              <ArrowRight size={18} />
            </a>
            <a href="/developer/examples" className="optionCard">
              <div>
                <span className="optionTitle">Examples</span>
                <p className="muted">Sample requests and payloads for core workflows and edge cases.</p>
              </div>
              <ArrowRight size={18} />
            </a>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Reference essentials</h2>
              <p className="muted">Important rules to keep every integration consistent and audit-friendly.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Always verify signatures</p>
                <p className="muted">Protect every callback and request with the required HMAC or token verification.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><FileJson2 size={18} /></div>
              <div>
                <p className="infoTitle">Use the documented schema</p>
                <p className="muted">Match payload fields and error semantics to avoid integration drift.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><BookOpenText size={18} /></div>
              <div>
                <p className="infoTitle">Keep versioning in view</p>
                <p className="muted">Review release notes and contract differences before upgrading production clients.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
