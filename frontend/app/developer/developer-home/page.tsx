'use client';

import { ArrowRight, Code2, KeyRound, Rocket, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function DeveloperHomePage() {
  return (
    <AccountPageShell
      title="Developer portal"
      subtitle="Secure APIs, integrations, and tooling for engineering teams building on PesaGuard."
      actions={
        <button type="button" className="buttonAccent">
          <Rocket size={16} /> Launch sandbox
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Overview</h2>
              <p className="muted">Everything your team needs to integrate, verify, and ship safely.</p>
            </div>
            <span className="badge">Live</span>
          </div>

          <div className="miniStatGrid">
            <div className="miniStat">
              <span>API status</span>
              <strong>99.98%</strong>
            </div>
            <div className="miniStat">
              <span>Webhook health</span>
              <strong>Healthy</strong>
            </div>
            <div className="miniStat">
              <span>Keys active</span>
              <strong>18</strong>
            </div>
            <div className="miniStat">
              <span>Latency</span>
              <strong>214ms</strong>
            </div>
          </div>

          <div className="optionList">
            <div className="optionCard activeCard">
              <div>
                <span className="optionTitle">Production API</span>
                <p className="muted">Fully operational and versioned for live payment orchestration.</p>
              </div>
              <ArrowRight size={18} />
            </div>
            <div className="optionCard">
              <div>
                <span className="optionTitle">Sandbox</span>
                <p className="muted">Test advanced flows without touching production records.</p>
              </div>
              <ArrowRight size={18} />
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Quick actions</h2>
              <p className="muted">Jump directly into the workflows your team uses most.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><KeyRound size={18} /></div>
              <div>
                <p className="infoTitle">Authentication</p>
                <p className="muted">Manage keys, OAuth scopes, and token rotation for secure access.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Code2 size={18} /></div>
              <div>
                <p className="infoTitle">API reference</p>
                <p className="muted">Review endpoints, examples, and request models with versioning context.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Security controls</p>
                <p className="muted">Monitor rate limits, callback verification, and trust policy updates.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
