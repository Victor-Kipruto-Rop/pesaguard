import { ArrowRight, ShieldCheck, Smartphone } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthVerifyPhonePage() {
  return (
    <AuthPageShell
      eyebrow="Secure recovery"
      title="Verify your phone"
      subtitle="Enter the code sent to your trusted mobile device to confirm recovery access."
      footer={
        <p className="authPrompt">
          Need another code? <a href="/auth/verify-phone">Send again</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Enter verification code</h3>
          <p>Use the 6-digit code sent to +254 712 345 678.</p>
        </div>

        <div className="authCodeRow">
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="4" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="1" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="9" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="2" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="7" />
          <input className="authCodeInput" type="text" maxLength={1} defaultValue="6" />
        </div>

        <button type="submit" className="authButton primary">
          <Smartphone size={18} /> Verify phone
          <ArrowRight size={18} />
        </button>

        <div className="authSummaryCard">
          <strong><ShieldCheck size={16} /> Trusted device check</strong>
          <p>This step helps make sure the phone linked to your account is still under your control.</p>
        </div>
      </form>
    </AuthPageShell>
  );
}
