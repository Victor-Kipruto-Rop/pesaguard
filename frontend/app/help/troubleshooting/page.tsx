import { AlertTriangle, ArrowRight, CheckCircle2, ServerCrash, ShieldAlert } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function HelpTroubleshootingPage() {
  return (
    <AccountPageShell
      title="Troubleshooting"
      subtitle="Use guided checks for authorization issues, failed payouts, delayed syncs, and data mismatches."
      actions={
        <a href="/help/contact-support" className="buttonGhost">
          <ShieldAlert size={16} /> Escalate issue
        </a>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Common root causes</h2>
              <p className="muted">Quick checks to isolate the source of disruption before escalation.</p>
            </div>
            <span className="badge">Checks</span>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><AlertTriangle size={18} /></div>
              <div>
                <p className="infoTitle">Failed transaction retries</p>
                <p className="muted">Review the transaction state, API response, and retry limit metadata before resubmitting.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ServerCrash size={18} /></div>
              <div>
                <p className="infoTitle">Synced data delays</p>
                <p className="muted">Check queue health, ingestion timestamps, and downstream worker status in the system dashboard.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Access denials</p>
                <p className="muted">Review tenant membership, role assignment, and MFA-verification state before requesting help.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Recommended flow</h2>
              <p className="muted">A structured path to isolate the issue and resolve it faster.</p>
            </div>
          </div>

          <div className="toggleList">
            <div className="toggleRow active">
              <div>
                <strong>1. Verify the issue scope</strong>
                <p>Confirm whether it impacts one account, one tenant, or the whole platform.</p>
              </div>
              <span className="statusPill success">Done</span>
            </div>
            <div className="toggleRow active">
              <div>
                <strong>2. Check service health</strong>
                <p>Review the live status, queue depth, and recent incident reports.</p>
              </div>
              <span className="statusPill success">Next</span>
            </div>
            <div className="toggleRow">
              <div>
                <strong>3. Open a support ticket</strong>
                <p>Include timestamps, IDs, and screenshots to reduce triage time.</p>
              </div>
               <span className="statusPill">Queued</span>
            </div>
          </div>

          <div className="featureBadge">
            <ArrowRight size={16} /> Most issues are resolved in under one review pass with the right diagnostic data
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
