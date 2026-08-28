import { ArrowRight, Building2, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthChooseOrganizationPage() {
  return (
    <AuthPageShell
      eyebrow="Workspace"
      title="Choose your organization"
      subtitle="Select the tenant or business account you want to access before continuing." 
      footer={
        <p className="authPrompt">
          Need a different account? <a href="/auth/login">Return to sign in</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Organizations</h3>
          <p>Pick the workspace tied to your team’s operations.</p>
        </div>

        <div className="authList">
          <button type="button" className="authChoiceCard">
            <div>
              <strong>PesaGuard East Africa</strong>
              <span>Primary operational tenant</span>
            </div>
            <span className="authStatusPill">Active</span>
          </button>

          <button type="button" className="authChoiceCard">
            <div>
              <strong>Northstar Finance</strong>
              <span>Finance and compliance team</span>
            </div>
            <span className="authStatusPill">Active</span>
          </button>

          <button type="button" className="authChoiceCard">
            <div>
              <strong>Operations Sandbox</strong>
              <span>Training and testing workspace</span>
            </div>
            <span className="authStatusPill">Read-only</span>
          </button>
        </div>

        <button type="submit" className="authButton primary">
          <Building2 size={18} /> Continue
          <ArrowRight size={18} />
        </button>

        <div className="authSummaryCard">
          <strong><ShieldCheck size={16} /> Access control</strong>
          <p>Your permissions are evaluated before the selected organization opens.</p>
        </div>
      </form>
    </AuthPageShell>
  );
}
