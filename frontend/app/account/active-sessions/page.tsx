import { RefreshCw, ShieldCheck, Users, Zap, CheckCircle2, Globe2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountActiveSessionsPage() {
  return (
    <AccountPageShell
      title="Active Sessions"
      subtitle="Securely review the live session state and access controls for your account."
      actions={
        <button type="button" className="buttonGhost">
          <RefreshCw size={16} /> Refresh view
        </button>
      }
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Live session monitoring</h2>
              <p className="muted">A premium interface for session security and access visibility.</p>
            </div>
            <span className="badge">Realtime</span>
          </div>

          <div className="statusGrid">
            <div className="statusTile">
              <span className="statusLabel">Active sessions</span>
              <strong>03</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Users online</span>
              <strong>02</strong>
            </div>
            <div className="statusTile">
              <span className="statusLabel">Suspicious access</span>
              <strong>00</strong>
            </div>
          </div>

          <div className="sessionList">
            <div className="sessionRow">
              <div>
                <strong>Operations dashboard</strong>
                <span>MacBook Pro • Nairobi • 9 mins ago</span>
              </div>
              <span className="statusPill success">Healthy</span>
            </div>
            <div className="sessionRow">
              <div>
                <strong>Mobile access</strong>
                <span>iPhone 15 • Nairobi • 2 hrs ago</span>
              </div>
              <span className="statusPill success">Healthy</span>
            </div>
            <div className="sessionRow">
              <div>
                <strong>Legacy browser login</strong>
                <span>Windows laptop • Last seen 14 days ago</span>
              </div>
              <button type="button" className="inlineAction">End</button>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Security posture</h2>
              <p className="muted">Keep session access limited to trusted devices and locations.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Users size={18} /></div>
              <div>
                <p className="infoTitle">Centralized user control</p>
                <p className="muted">Assign access policies for every session in one place.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><ShieldCheck size={18} /></div>
              <div>
                <p className="infoTitle">Elevated protection</p>
                <p className="muted">Trusted sessions are segmented from high-risk access flows.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Globe2 size={18} /></div>
              <div>
                <p className="infoTitle">Location oversight</p>
                <p className="muted">Track session origin and flag unusual network activity promptly.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Operational visibility</p>
                <p className="muted">Track session metrics without overwhelming the interface.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
