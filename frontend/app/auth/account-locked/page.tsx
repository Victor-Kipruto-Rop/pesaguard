import { ArrowRight, Lock, ShieldAlert } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthAccountLockedPage() {
  return (
    <AuthPageShell
      eyebrow="Security notice"
      title="Account temporarily locked"
      subtitle="Multiple failed sign-in attempts were detected, and the account is currently protected pending review."
      footer={
        <p className="authPrompt">
          Need help right away? <a href="/help/contact-support">Contact support</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Access restricted</h3>
          <p>To regain access, verify your identity or request a manual review.</p>
        </div>

        <div className="authSummaryCard">
          <strong><ShieldAlert size={16} /> Security safeguard</strong>
          <p>This lock helps protect your account from unauthorized access and high-risk login attempts.</p>
        </div>

        <button type="submit" className="authButton primary">
          <Lock size={18} /> Unlock account
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
