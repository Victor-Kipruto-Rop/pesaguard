import { ArrowRight, CopyCheck, ShieldCheck } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthBackupCodesPage() {
  return (
    <AuthPageShell
      eyebrow="Recovery"
      title="Backup codes"
      subtitle="Store these codes in a safe place so you can regain access if your authenticator is unavailable."
      footer={
        <p className="authPrompt">
          Need to set up MFA again? <a href="/auth/two-factor-auth">Try verifier setup</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Recovery codes</h3>
          <p>Use one code per emergency access event. Do not share them.</p>
        </div>

        <div className="authSummaryCard">
          <strong><CopyCheck size={16} /> Save these securely</strong>
          <p>G7B-2QJY · P3LQ-44TK · K19D-AF6N · 2C5R-N7H8 · X4P1-8WQ2</p>
        </div>

        <button type="submit" className="authButton primary">
          <ShieldCheck size={18} /> I’ve saved them
          <ArrowRight size={18} />
        </button>
      </form>
    </AuthPageShell>
  );
}
