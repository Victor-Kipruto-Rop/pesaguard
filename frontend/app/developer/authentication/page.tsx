'use client';

import { ArrowRight, KeyRound, LockKeyhole, ShieldCheck, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AuthenticationPage() {
  return (
    <AccountPageShell
      title="Authentication"
      subtitle="Configure secure access patterns for your API clients and automation workflows."
      actions={
        <button type="button" className="buttonGhost">
          <ShieldCheck size={16} /> Rotate keys
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Credential strategy</h2>
              <p className="muted">Use strong identities and limited scopes to keep access auditable.</p>
            </div>
            <span className="badge">Protected</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="auth-type">Default auth type</label>
              <select id="auth-type" className="selectInput" defaultValue="oauth2">
                <option value="oauth2">OAuth 2.0</option>
                <option value="jwt">JWT bearer tokens</option>
                <option value="api-key">API key</option>
              </select>
            </div>
            <div className="fieldGroup">
              <label htmlFor="audience">Audience</label>
              <input id="audience" className="textInput" type="text" defaultValue="pesaguard-production" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="rotation">Rotation window</label>
              <input id="rotation" className="textInput" type="text" defaultValue="90 days" />
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <LockKeyhole size={16} /> Save security policy
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Active credentials</h2>
              <p className="muted">Current access identities with their trust and validity status.</p>
            </div>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Primary service account</strong>
                  <span className="statusPill success">Active</span>
                </div>
                <p>Payments API · Read/write access · Rotates every 90 days</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Partner OAuth client</strong>
                  <span className="statusPill">Review</span>
                </div>
                <p>Limited merchant access · Fresh token expiry scheduled in 12 days</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Internal admin token</strong>
                  <span className="statusPill success">Live</span>
                </div>
                <p>Restricted to control-plane endpoints and support tooling</p>
              </div>
            </div>
          </div>

          <div className="featureBadge">
            <Sparkles size={16} /> Multi-factor verification is enforced on all privileged tokens
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
