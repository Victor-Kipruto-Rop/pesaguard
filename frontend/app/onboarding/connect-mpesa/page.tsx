import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingConnectMpesaPage() {
  return (
    <OnboardingLayout title="Connect M-Pesa" step={6} total={10}>
      <div>
        <p className="muted">Connect your M-Pesa credentials to enable live transaction imports.</p>
        <div className="card-body">Credentials and sandbox options will be configured here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/connect-bank" next="/onboarding/invite-team" />
    </OnboardingLayout>
  );
}
