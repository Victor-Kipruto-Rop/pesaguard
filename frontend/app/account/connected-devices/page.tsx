import { Laptop, Smartphone, ShieldCheck, Zap, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountConnectedDevicesPage() {
  return (
    <AccountPageShell
      title="Connected Devices"
      subtitle="Review devices that have access to your account and revoke unwanted connections."
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Device overview</h2>
              <p className="muted">A clear view into the endpoints with active access privileges.</p>
            </div>
            <button type="button" className="buttonGhost">
              <Zap size={16} /> Refresh
            </button>
          </div>

          <div className="listCardPanel">
            <div className="listCardItem">
              <div className="listCardIcon brandIcon"><Laptop size={18} /></div>
              <div className="listCardText">
                <strong>MacBook Pro – Nairobi Office</strong>
                <span>Chrome on macOS • Last active 9 minutes ago</span>
              </div>
              <span className="statusPill success">Trusted</span>
            </div>

            <div className="listCardItem">
              <div className="listCardIcon accentIcon"><Smartphone size={18} /></div>
              <div className="listCardText">
                <strong>iPhone 15 – Victor’s Primary</strong>
                <span>iOS • Last active 2 hours ago</span>
              </div>
              <span className="statusPill success">Verified</span>
            </div>

            <div className="listCardItem mutedItem">
              <div className="listCardIcon brandIcon"><Laptop size={18} /></div>
              <div className="listCardText">
                <strong>Windows laptop – Legacy access</strong>
                <span>Edge on Windows • Last active 14 days ago</span>
              </div>
              <button type="button" className="inlineAction">Revoke</button>
            </div>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Secure devices</h2>
              <p className="muted">Keep only trusted devices connected to your workspace.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Laptop size={18} /></div>
              <div>
                <p className="infoTitle">Desktop access</p>
                <p className="muted">Monitor browser and desktop sessions in one location.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Smartphone size={18} /></div>
              <div>
                <p className="infoTitle">Mobile sessions</p>
                <p className="muted">Easily revoke mobile access if a device is lost or reassigned.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Trust score</p>
                <p className="muted">All current sessions are within the approved device policy range.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
