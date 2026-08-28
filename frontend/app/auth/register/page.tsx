import { ArrowRight, Check, ShieldCheck, UserRound } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthRegisterPage() {
  return (
    <AuthPageShell
      eyebrow="Create account"
      title="Set up your workspace"
      subtitle="Launch a secure tenant and start coordinating operational oversight from one place."
      footer={
        <p className="authPrompt">
          Already have an account? <a href="/auth/login">Sign in</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Register</h3>
          <p>Start with your work details and configure the security baseline.</p>
        </div>

        <div className="authInputGroup">
          <label htmlFor="register-name">Full name</label>
          <input id="register-name" className="authInput" type="text" placeholder="Victor Otieno" />
        </div>

        <div className="authInputGroup">
          <label htmlFor="register-email">Work email</label>
          <input id="register-email" className="authInput" type="email" placeholder="name@company.com" />
        </div>

        <div className="authInputGroup">
          <label htmlFor="register-password">Password</label>
          <input id="register-password" className="authInput" type="password" placeholder="Create a secure password" />
        </div>

        <div className="authInputGroup">
          <label htmlFor="register-confirm">Confirm password</label>
          <input id="register-confirm" className="authInput" type="password" placeholder="Repeat your password" />
        </div>

        <div className="checkboxRow">
          <label className="authCheckbox">
            <input type="checkbox" defaultChecked />
            <span>I agree to the terms</span>
          </label>
          <ShieldCheck size={18} color="#1f7a5d" />
        </div>

        <button type="submit" className="authButton primary">
          <UserRound size={18} /> Create account
          <ArrowRight size={18} />
        </button>

        <div className="authSummaryCard">
          <strong><Check size={16} /> Security baseline</strong>
          <p>Multi-factor authentication is enabled by default for new tenant accounts.</p>
        </div>
      </form>
    </AuthPageShell>
  );
}
