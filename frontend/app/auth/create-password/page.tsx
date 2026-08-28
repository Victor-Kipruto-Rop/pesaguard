import { ArrowRight, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthCreatePasswordPage() {
  return (
    <AuthPageShell
      eyebrow="Setup"
      title="Create your password"
      subtitle="Finish onboarding by creating a password that meets your account’s security baseline."
      footer={
        <p className="authPrompt">
          Need account help? <a href="/help/contact-support">Contact support</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Set password</h3>
          <p>Use a unique password to protect your workspace and linked permissions.</p>
        </div>

        <div className="authInputGroup">
          <label htmlFor="create-password">Password</label>
          <input id="create-password" className="authInput" type="password" placeholder="Create password" />
        </div>

        <div className="authInputGroup">
          <label htmlFor="create-password-confirm">Confirm password</label>
          <input id="create-password-confirm" className="authInput" type="password" placeholder="Repeat password" />
        </div>

        <button type="submit" className="authButton primary">
          <ShieldCheck size={18} /> Continue
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
