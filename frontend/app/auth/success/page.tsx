import { ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthSuccessPage() {
  return (
    <AuthPageShell
      eyebrow="Success"
      title="Everything is set"
      subtitle="Your account setup is complete and your operations workspace is ready for secure access."
      footer={
        <p className="authPrompt">
          Continue to <a href="/admin">dashboard</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Setup complete</h3>
          <p>Your onboarding flow finished successfully and the workspace is ready to use.</p>
        </div>

        <div className="authSummaryCard">
          <strong><CheckCircle2 size={16} /> Verified</strong>
          <p>All required protections are enabled, including secure access and operational access control.</p>
        </div>

        <button type="submit" className="authButton primary">
          <Sparkles size={18} /> Go to dashboard
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
