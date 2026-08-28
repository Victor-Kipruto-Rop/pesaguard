'use client';

import { ArrowRight, Blocks, Code2, Play, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function ExamplesPage() {
  return (
    <AccountPageShell
      title="Examples"
      subtitle="Reference implementation patterns for integrations, API usage, and secure event handling."
      actions={
        <button type="button" className="buttonAccent">
          <Play size={16} /> Run example
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Integration patterns</h2>
              <p className="muted">Use these reference flows as a starting point for production integrations.</p>
            </div>
            <span className="badge">SDK ready</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><Code2 size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Payment initiation</strong>
                  <span className="statusPill success">Ready</span>
                </div>
                <p>Create a payment request, handle callbacks, and reconcile state transitions.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Blocks size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Webhook consumption</strong>
                  <span className="statusPill">Secure</span>
                </div>
                <p>Verify signatures, deduplicate payloads, and record outcomes.</p>
              </div>
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><ShieldCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Token refresh flow</strong>
                  <span className="statusPill success">Enabled</span>
                </div>
                <p>Rotate OAuth credentials without breaking active sessions or automation jobs.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Sample payload</h2>
              <p className="muted">Typical response structure from the platform.</p>
            </div>
          </div>

          <div className="placeholderPanel">
            <div className="placeholderHeader">Event response</div>
            <div className="placeholderRows">
              <div className="placeholderRow" />
              <div className="placeholderRow" />
              <div className="placeholderRow" />
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> These examples match the live API contract conventions
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
