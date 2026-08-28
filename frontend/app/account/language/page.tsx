import { Globe2, Languages, CheckCircle2 } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountLanguagePage() {
  return (
    <AccountPageShell
      title="Language"
      subtitle="Select your interface language for a smooth localized experience."
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Preferred language</h2>
              <p className="muted">Switch between available locale options for your account.</p>
            </div>
            <span className="badge">Default</span>
          </div>

          <div className="optionList">
            <button type="button" className="optionCard activeCard">
              <div>
                <span className="optionTitle">English</span>
                <p className="muted">Global default for PesaGuard operations and compliance workflows.</p>
              </div>
              <Languages size={20} />
            </button>
            <button type="button" className="optionCard">
              <div>
                <span className="optionTitle">Swahili</span>
                <p className="muted">Localized experience for East African teams and regional operations.</p>
              </div>
              <Globe2 size={20} />
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Localization</h2>
              <p className="muted">Language selection influences labels, alerts, and interface tone.</p>
            </div>
          </div>

          <div className="infoList elevatedList">
            <div className="infoRow">
              <div className="infoIcon brandIcon"><Globe2 size={18} /></div>
              <div>
                <p className="infoTitle">Consistent terminology</p>
                <p className="muted">Avoid confusion during audits, escalations, and support handoffs.</p>
              </div>
            </div>
            <div className="infoRow">
              <div className="infoIcon successIcon"><CheckCircle2 size={18} /></div>
              <div>
                <p className="infoTitle">Regional alignment</p>
                <p className="muted">The operating language remains aligned with your team’s working culture.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
