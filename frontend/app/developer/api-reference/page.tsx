'use client';

import { ArrowRight, Braces, ChevronRight, Database, Play } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function ApiReferencePage() {
  return (
    <AccountPageShell
      title="API reference"
      subtitle="Browse the live contract surface for payment flows, reconciliation events, and platform resources."
      actions={
        <button type="button" className="buttonAccent">
          <Play size={16} /> Try request
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Endpoint catalog</h2>
              <p className="muted">Stable resources grouped by operational domain.</p>
            </div>
            <span className="badge">v2.4</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><Database size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>GET /v2/payments</strong>
                  <span className="statusPill success">Stable</span>
                </div>
                <p>List settlement and payout transactions with filters by status, wallet, and date range.</p>
              </div>
              <ChevronRight size={18} />
            </div>
            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Braces size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>POST /v2/reconciliation</strong>
                  <span className="statusPill">Preview</span>
                </div>
                <p>Trigger a reconciliation run and receive disposition metadata for matched records.</p>
              </div>
              <ChevronRight size={18} />
            </div>
            <div className="stackCard">
              <div className="stackCardIcon brandIcon"><Database size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>GET /v2/members/{'{id}'}</strong>
                  <span className="statusPill success">Stable</span>
                </div>
                <p>Fetch member identity, risk classification, and account summary information.</p>
              </div>
              <ChevronRight size={18} />
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Request model</h2>
              <p className="muted">Consistent response semantics and error handling.</p>
            </div>
          </div>

          <div className="placeholderPanel">
            <div className="placeholderHeader">Response envelope</div>
            <div className="placeholderRows">
              <div className="placeholderRow" />
              <div className="placeholderRow" />
              <div className="placeholderRow" />
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> Rate limits are enforced at 600 requests per minute per key
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
