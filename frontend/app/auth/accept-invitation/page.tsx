import { ArrowRight, CheckCircle2, Users } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthAcceptInvitationPage() {
  return (
    <AuthPageShell
      eyebrow="Invitation"
      title="Accept your invitation"
      subtitle="You’ve been invited into a secure workspace. Confirm your details and start collaborating."
      footer={
        <p className="authPrompt">
          Already have an account? <a href="/auth/login">Sign in</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Team access</h3>
          <p>PesaGuard East Africa has invited you to join this tenant.</p>
        </div>

        <div className="authSummaryCard">
          <strong><Users size={16} /> Organization</strong>
          <p>PesaGuard East Africa · Operations + risk oversight</p>
        </div>

        <button type="submit" className="authButton primary">
          <CheckCircle2 size={18} /> Accept invitation
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
