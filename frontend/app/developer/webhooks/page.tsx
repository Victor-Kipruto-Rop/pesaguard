'use client';

import { ArrowRight, BellRing, CheckCircle2, Clock3, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function WebhooksPage() {
  return (
    <AccountPageShell
      title="Webhooks"
      subtitle="Monitor delivery health, validate event integrity, and keep downstream systems synchronized in real time."
      actions={
        <button type="button" className="buttonAccent">
          <BellRing size={16} /> Add endpoint
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Endpoint health</h2>
              <p className="muted">Event delivery state across all configured webhook destinations.</p>
            </div>
            <span className="badge">Healthy</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Delivered</span>
              <strong>98.7%</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Retries</span>
              <strong>24</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Lag</span>
              <strong>1.3s</strong>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Recent delivery success</p>
                <p className="muted">The latest payment events were accepted and processed without validation errors.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Clock3 size={18} /></div>
              <div>
                <p className="infoTitle">Retry schedule</p>
                <p className="muted">Failed callback attempts are queued with exponential backoff and retry tracing.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Signature validation</p>
                <p className="muted">Every payload is authenticated using the configured signing secret.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Configured endpoints</h2>
              <p className="muted">Event subscriptions active across your operational systems.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Payment status updates</strong>
                <p>Triggered on success, reversal, and retry events.</p>
              </div>
              <span className="statusPill success">Live</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Settlement notifications</strong>
                <p>Sent when funds clear or account balances are adjusted.</p>
              </div>
              <span className="statusPill success">Live</span>
            </div>
            <div className="toggleRow">
              <div>
                <strong>Risk event stream</strong>
                <p>Reserved for internal monitoring and exception-driven playbooks.</p>
              </div>
              <span className="statusPill">Paused</span>
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> All active webhooks are verified and signed before dispatch
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
