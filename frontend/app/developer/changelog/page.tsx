'use client';

import { ArrowRight, CalendarClock, GitBranch, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function ChangelogPage() {
  return (
    <AccountPageShell
      title="Changelog"
      subtitle="Track the latest product changes, reliability improvements, and platform updates."
      actions={
        <button type="button" className="buttonGhost">
          <GitBranch size={16} /> View releases
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Latest release</h2>
              <p className="muted">Shipping stability, API clarity, and stronger operational safeguards.</p>
            </div>
            <span className="badge">v2.4.1</span>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><Sparkles size={18} /></div>
              <div>
                <p className="infoTitle">Improved event reliability</p>
                <p className="muted">Added stronger retry logic and more resilient callback replay handling.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><CalendarClock size={18} /></div>
              <div>
                <p className="infoTitle">API documentation cleanup</p>
                <p className="muted">Updated request/response examples and clarified default parameter behavior.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon brandIcon"><GitBranch size={18} /></div>
              <div>
                <p className="infoTitle">Operational improvements</p>
                <p className="muted">Adjusted rate-limit monitoring and surfaced better queue health signals.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recent updates</h2>
              <p className="muted">A rolling view of the project’s recent milestones.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>Webhook signature validation</strong>
                <p>Improved rejection handling for malformed payloads and replay attempts.</p>
              </div>
              <span className="statusPill success">Added</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>SDK polish</strong>
                <p>Minor fixes to sample auth flows and error handling in client libraries.</p>
              </div>
              <span className="statusPill success">Updated</span>
            </div>
            <div className="toggleRow">
              <div>
                <strong>Reconciliation dashboard</strong>
                <p>Expanded search fields and improved exported summary reporting.</p>
              </div>
              <span className="statusPill">Queued</span>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
