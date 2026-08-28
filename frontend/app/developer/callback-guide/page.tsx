'use client';

import { ArrowRight, BellRing, CheckCircle2, ShieldCheck, Waypoints } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function CallbackGuidePage() {
  return (
    <AccountPageShell
      title="Callback guide"
      subtitle="Build and verify webhook integrations that keep your platform synchronized with real-time payment events."
      actions={
        <button type="button" className="buttonGhost">
          <BellRing size={16} /> Validate endpoint
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Delivery flow</h2>
              <p className="muted">Secure callbacks are signed, retried, and monitored end-to-end.</p>
            </div>
            <span className="badge">Verified</span>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Create signature</p>
                <p className="muted">Verify the HMAC signature before processing any event payload.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Waypoints size={18} /></div>
              <div>
                <p className="infoTitle">Handle retries</p>
                <p className="muted">Queue retries with exponential backoff for transient network failures.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Confirm delivery</p>
                <p className="muted">Ack only when the payload has been idempotently persisted and processed.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Callback configuration</h2>
              <p className="muted">Production setup with endpoint security and retry policy.</p>
            </div>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="callback-url">Endpoint URL</label>
              <input id="callback-url" className="textInput" type="text" defaultValue="https://api.example.com/webhooks/pesaguard" />
            </div>
            <div className="fieldGroup">
              <label htmlFor="event-type">Active event types</label>
              <select id="event-type" className="selectInput" defaultValue="all">
                <option value="all">All payment events</option>
                <option value="payments">Payments only</option>
                <option value="reconciliation">Reconciliation only</option>
              </select>
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> Security header validation is enabled and active
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
