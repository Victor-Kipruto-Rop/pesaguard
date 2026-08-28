import { ShieldCheck, Key, Lock, ShieldAlert, Fingerprint, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountSecurityPage() {
  return (
    <AccountPageShell
      title="Security"
      subtitle="Review your account protection settings and strengthen your access posture."
      actions={
        <button type="button" className="buttonGhost">
          <ShieldCheck size={16} /> Security review
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Protection controls</h2>
              <p className="muted">Control authentication, trust signals, and access risk from one place.</p>
            </div>
            <span className="badge">Strong</span>
          </div>

          <div className="stackCardList">
            <div className="stackCard stateSafe">
              <div className="stackCardIcon brandIcon"><Lock size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Password policy</strong>
                  <span className="statusPill success">Active</span>
                </div>
                <p className="muted">Strong password enforcement with 90-day rotation and breach monitoring.</p>
              </div>
            </div>

            <div className="stackCard stateSafe">
              <div className="stackCardIcon successIcon"><Key size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Two-factor authentication</strong>
                  <span className="statusPill success">Verified</span>
                </div>
                <p className="muted">Protect login events with authenticator verification and device trust checks.</p>
              </div>
            </div>

            <div className="stackCard">
              <div className="stackCardIcon accentIcon"><Fingerprint size={18} /></div>
              <div className="stackCardBody">
                <div className="stackCardHeader">
                  <strong>Risk-based access</strong>
                  <span className="statusPill">Monitored</span>
                </div>
                <p className="muted">Unusual sign-ins are flagged for review before extended access is granted.</p>
              </div>
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <ShieldAlert size={16} /> Strengthen security
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Audit readiness</h2>
              <p className="muted">Security controls should be visible, measurable, and easy to validate.</p>
            </div>
          </div>

          <div className="miniStatGrid">
            <div className="miniStat">
              <span>Session review</span>
              <strong>3 min</strong>
            </div>
            <div className="miniStat">
              <span>Last review</span>
              <strong>Today</strong>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon accentIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Session termination</p>
                <p className="muted">Revoke sessions immediately if you suspect compromise or unusual activity.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Access compliance</p>
                <p className="muted">Your account policy remains aligned with the latest security standards.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
