import { ArrowRight, Mail } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthForgotPasswordPage() {
  return (
    <AuthPageShell
      eyebrow="Recovery"
      title="Reset your password"
      subtitle="We’ll send a secure reset link to the email on your profile so you can regain access quickly."
      footer={
        <p className="authPrompt">
          Remembered your password? <a href="/auth/login">Back to sign in</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Forgot password</h3>
          <p>Enter the email address associated with your account.</p>
        </div>

        <div className="authInputGroup">
          <label htmlFor="reset-email">Email address</label>
          <input id="reset-email" className="authInput" type="email" placeholder="name@company.com" />
        </div>

        <button type="submit" className="authButton primary">
          <Mail size={18} /> Send reset link
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
