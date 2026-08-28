'use client';

import { ArrowRight, FlaskConical, Rocket, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function SandboxPage() {
  return (
    <AccountPageShell
      title="Sandbox"
      subtitle="Prototype payment flows, test event handling, and validate new integrations safely before production rollout."
      actions={
        <button type="button" className="buttonAccent">
          <Rocket size={16} /> Start session
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Environment status</h2>
              <p className="muted">Live sandbox controls for testing and validation work.</p>
            </div>
            <span className="badge">Online</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="sandbox-environment">Environment</label>
              <select id="sandbox-environment" className="selectInput" defaultValue="staging">
                <option value="staging">Staging</option>
                <option value="preview">Preview</option>
                <option value="qa">QA</option>
              </select>
            </div>
            <div className="fieldGroup">
              <label htmlFor="sandbox-version">API version</label>
              <input id="sandbox-version" className="textInput" type="text" defaultValue="v2.4-preview" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <FlaskConical size={16} /> Refresh sandbox
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Current readiness</h2>
              <p className="muted">The sandbox is ready for secure, isolated integration playbooks.</p>
            </div>
          </div>

          <div className="miniStatGrid">
            <div className="miniStat">
              <span>Sessions</span>
              <strong>12</strong>
            </div>
            <div className="miniStat">
              <span>Events</span>
              <strong>4,892</strong>
            </div>
            <div className="miniStat">
              <span>Callback tests</span>
              <strong>94%</strong>
            </div>
            <div className="miniStat">
              <span>Uptime</span>
              <strong>100%</strong>
            </div>
          </div>

          <div className="featureBadge">
            <ShieldCheck size={16} /> Isolation safeguards are enabled for every active sandbox session
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
