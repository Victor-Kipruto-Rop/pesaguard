import { ArrowRight, Lock } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthResetPasswordPage() {
  return (
    <AuthPageShell
      eyebrow="Secure reset"
      title="Choose a new password"
      subtitle="Create a strong password that protects your account and all linked operational access."
      footer={
        <p className="authPrompt">
          Need help? <a href="/auth/forgot-password">Request another reset</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>New password</h3>
          <p>Use at least 12 characters with a mix of letters, numbers, and symbols.</p>
        </div>

        <div className="authInputGroup">
          <label htmlFor="new-password">New password</label>
          <input id="new-password" className="authInput" type="password" placeholder="Enter a new password" />
        </div>

        <div className="authInputGroup">
          <label htmlFor="confirm-new-password">Confirm password</label>
          <input id="confirm-new-password" className="authInput" type="password" placeholder="Repeat the password" />
        </div>

        <button type="submit" className="authButton primary">
          <Lock size={18} /> Update password
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
