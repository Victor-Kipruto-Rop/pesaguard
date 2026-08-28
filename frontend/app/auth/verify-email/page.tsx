import { ArrowRight, MailCheck, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthVerifyEmailPage() {
  return (
    <AuthPageShell
      eyebrow="Verification"
      title="Verify your email"
      subtitle="We sent a secure confirmation link to your inbox to complete account activation."
      footer={
        <p className="authPrompt">
          Didn’t receive it? <a href="/auth/verify-email">Resend email</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Check your inbox</h3>
          <p>Open the message from PesaGuard and complete verification to continue.</p>
        </div>

        <div className="authSummaryCard">
          <strong><MailCheck size={16} /> Delivery status</strong>
          <p>Verification was sent to <strong>victor@pesaguard.co</strong>.</p>
        </div>

        <button type="submit" className="authButton primary">
          <ShieldCheck size={18} /> Confirm email
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
