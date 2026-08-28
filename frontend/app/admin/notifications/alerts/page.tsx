'use client';

import { AlertTriangle, ShieldCheck } from 'lucide-react';
import PageHeader from '../../../../components/PageHeader';

export default function AlertsPage() {
  return (
    <main className="shell">
      <PageHeader eyebrow="Admin" title="Alerts" summary="Tenant administration view for this module." />

      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Active alerts</h2>
              <p className="muted">Critical alerts across tenants and integrations.</p>
            </div>
            <span className="badge">3 critical</span>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon warningIcon"><AlertTriangle size={18} /></div>
              <div>
                <p className="infoTitle">High failure rate</p>
                <p className="muted">Monitor delivery failures and escalation status per tenant.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Escalation policies</h2>
              <p className="muted">Manage how alerts are escalated and which teams receive them.</p>
            </div>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><ShieldCheck size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Auto-escalate to on-call</strong>
                  <span className="statusPill success">Enabled</span>
                </div>
                <p>Alerts exceeding thresholds are routed automatically to the on-call rotation.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
