import { ArrowLeft, ShieldAlert } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';

export default function AuthUnauthorizedPage() {
  return (
    <AuthPageShell
      eyebrow="Access denied"
      title="You are not authorized"
      subtitle="This workspace requires the correct permissions before you can continue with operational tasks."
      footer={
        <p className="authPrompt">
          Return to <a href="/auth/login">sign in</a>
        </p>
      }
    >
      <form className="authForm">
        <div className="authFormHeader">
          <h3>Permission required</h3>
          <p>Your current role does not grant access to this section.</p>
        </div>

        <div className="authSummaryCard">
          <strong><ShieldAlert size={16} /> Role check</strong>
          <p>Contact your administrator to request the required permissions or access level.</p>
        </div>

        <button type="button" className="authButton primary">
          <ArrowLeft size={18} /> Back to sign in
        </button>
      </form>
    </AuthPageShell>
  );
}
