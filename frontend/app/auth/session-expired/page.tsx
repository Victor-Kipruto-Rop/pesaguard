import { ArrowRight, RefreshCw, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthSessionExpiredPage() {
  return (
    <AuthPageShell
      eyebrow="Session timeout"
      title="Your session expired"
      subtitle="For security reasons, your active session has ended. Please sign in again to continue working."
      footer={
        <p className="authPrompt">
          Want to continue? <a href="/auth/login">Sign in again</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Reconnect securely</h3>
          <p>Your access was automatically terminated after a period of inactivity.</p>
        </div>

        <div className="authSummaryCard">
          <strong><ShieldCheck size={16} /> Security status</strong>
          <p>No sensitive actions were completed after the timeout, and your session remains protected.</p>
        </div>

        <button type="submit" className="authButton primary">
          <RefreshCw size={18} /> Re-enter workspace
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
