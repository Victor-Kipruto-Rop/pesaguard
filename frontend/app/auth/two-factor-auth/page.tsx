import { ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthTwoFactorAuthPage() {
  return (
    <AuthPageShell
      eyebrow="Verification"
      title="Two-factor authentication"
      subtitle="Complete your verification step to protect the account against unauthorized access."
      footer={
        <p className="authPrompt">
          Lost access? <a href="/auth/backup-codes">Use backup codes</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Enter code</h3>
          <p>Open your authenticator app and enter the 6-digit code.</p>
        </div>

        <div className="authCodeRow">
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="7" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="2" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="4" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="9" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="1" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="8" />
        </div>

        <button type="submit" className="authButton primary">
          <ShieldCheck size={18} /> Verify account
          <ArrowRight size={18} />
        </button>

        <div className="authSummaryCard">
          <strong><CheckCircle2 size={16} /> Trusted access</strong>
          <p>Your login is protected by a second proof of identity before any critical action is allowed.</p>
        </div>
      </form>
    </AuthPageShell>
  );
}
