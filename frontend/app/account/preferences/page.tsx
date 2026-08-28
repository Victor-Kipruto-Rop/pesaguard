import { Settings, Bell, Moon, LayoutGrid, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountPreferencesPage() {
  return (
    <AccountPageShell
      title="Preferences"
      subtitle="Tailor PesaGuard to your personal workflow and notification style."
    >
      <div className="panelGrid">
        <section className="sectionPanel formPanel">
          <div className="panelHeader">
            <div>
              <h2>Interface preferences</h2>
              <p className="muted">Set the environment to match your operating rhythm.</p>
            </div>
            <span className="badge">Active</span>
          </div>

          <div className="optionList">
            <button type="button" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Compact layout</span>
                <p className="muted">Optimized for fast operational review and dense data work.</p>
              </div>
              <LayoutGrid size={20} />
            </button>
            <button type="button" className="optionCard">
              <div>
                <span className="optionTitle">Comfort view</span>
                <p className="muted">More spacing, softer tone, and reduced visual density.</p>
              </div>
              <Moon size={20} />
            </button>
          </div>

          <div className="featureBadge">
            <Sparkles size={16} /> Workflow tuned for executive monitoring
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Notification settings</h2>
              <p className="muted">Choose how you receive alerts and updates.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Bell size={18} /></div>
              <div>
                <p className="infoTitle">Alert experience</p>
                <p className="muted">Prefer minimal but priority-driven notifications for focused review.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon accentIcon"><Settings size={18} /></div>
              <div>
                <p className="infoTitle">Workflow aligned</p>
                <p className="muted">Keep preferences consistent with your security, audit, and operations team.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
