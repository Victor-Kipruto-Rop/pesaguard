'use client';

import { Activity, CheckCircle2, Clock3, Gauge, ShieldCheck } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function StatusPage() {
  return (
    <AccountPageShell
      title="System status"
      subtitle="Track the health, latency, and operational continuity of the platform in real time."
      actions={
        <button type="button" className="buttonGhost">
          <Activity size={16} /> View timeline
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Platform health</h2>
              <p className="muted">Current service conditions across the primary platform backbone.</p>
            </div>
            <span className="badge">Operational</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Availability</span>
              <strong>99.98%</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Transactions</span>
              <strong>3.2k</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Latency</span>
              <strong>214ms</strong>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Payment orchestration</p>
                <p className="muted">All primary routes processing normally with no incident degradation.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Gauge size={18} /></div>
              <div>
                <p className="infoTitle">Reconciliation queue</p>
                <p className="muted">Queue depth remains below threshold with active support automation.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Security checks</p>
                <p className="muted">Authentication, signature validation, and callback verification are green.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent events</h2>
              <p className="muted">Recent platform updates and operational changes.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Primary API restored</strong>
                <p>System load stabilized after the planned scaling event.</p>
              </div>
              <div className="toggleSwitch" />
            </div>
            <div className="toggleRow active">
              <div>
                <strong>Webhook latency normal</strong>
                <p>Delivery queue has returned below the alert threshold.</p>
              </div>
              <div className="toggleSwitch" />
            </div>
            <div className="toggleRow">
              <div>
                <strong>Maintenance window scheduled</strong>
                <p>Planned upgrade reserved for the next advisory window.</p>
              </div>
              <div className="toggleSwitch" />
            </div>
          </div>

          <div className="featureBadge">
            <Clock3 size={16} /> Last updated 4 minutes ago
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
