import { Clock3, MapPin, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountTimezonePage() {
  return (
    <AccountPageShell
      title="Timezone"
      subtitle="Set your preferred timezone for accurate timestamps and audit records."
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Timezone settings</h2>
              <p className="muted">Choose the correct locale for time-based event tracking.</p>
            </div>
            <span className="badge">Synced</span>
          </div>

          <div className="fieldGrid">
            <div className="fieldGroup">
              <label htmlFor="timezone">Timezone</label>
              <select id="timezone" className="selectInput" defaultValue="East Africa Time (EAT)">
                <option>East Africa Time (EAT)</option>
                <option>UTC</option>
                <option>WAT</option>
                <option>Central European Time</option>
              </select>
            </div>
          </div>

          <div className="formActions">
            <button type="button" className="buttonAccent">
              <MapPin size={16} /> Save timezone
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Timestamp clarity</h2>
              <p className="muted">Consistent timezone settings help audit and reconciliation workflows.</p>
            </div>
          </div>

          <div className="previewPanel">
            <div className="previewHeader">
              <div>
                <p className="previewLabel">Current clock</p>
                <h3>10:24 AM EAT</h3>
              </div>
              <Clock3 size={24} />
            </div>
            <div className="previewBody">
              <span className="pill">Local time</span>
              <p className="muted">All event timestamps are displayed in your selected zone.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Operational accuracy</p>
                <p className="muted">This setting ensures audit timelines match your team’s working day.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
