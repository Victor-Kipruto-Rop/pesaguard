import { Monitor, SunMoon, Sparkles } from 'lucide-react';
import AccountPageShell from '../../../components/AccountPageShell';

export default function AccountAppearancePage() {
  return (
    <AccountPageShell
      title="Appearance"
      subtitle="Refine the visual tone of your account so the console feels premium and uncluttered."
    >
      <div className="panelGrid">
        <section className="sectionPanel">
          <div className="panelHeader">
            <div>
              <h2>Theme settings</h2>
              <p className="muted">Choose the interface style most suitable for your workflow.</p>
            </div>
            <button type="button" className="buttonGhost">
              <SunMoon size={16} /> System mode
            </button>
          </div>

          <div className="optionList">
            <button type="button" className="optionCard activeCard">
              <div>
                <span className="optionTitle">Dark mode</span>
                <p className="muted">The default premium PesaGuard experience for high-focus operations.</p>
              </div>
              <Monitor size={20} />
            </button>
            <button type="button" className="optionCard">
              <div>
                <span className="optionTitle">Soft contrast</span>
                <p className="muted">Softer tones for longer review sessions and lower visual fatigue.</p>
              </div>
              <Sparkles size={20} />
            </button>
          </div>
        </section>

        <section className="sectionPanel highlightPanel">
          <div className="panelHeader">
            <div>
              <h2>Preview</h2>
              <p className="muted">A subtle interface helps you stay focused on security operations.</p>
            </div>
          </div>

          <div className="previewPanel">
            <div className="previewHeader">
              <div>
                <p className="previewLabel">Workspace</p>
                <h3>Secure session audit</h3>
              </div>
              <Monitor size={24} />
            </div>
            <div className="previewBody">
              <span className="pill">Premium</span>
              <p className="muted">This preview reflects the same tone used across your account pages.</p>
            </div>
          </div>
        </section>
      </div>
    </AccountPageShell>
  );
}
