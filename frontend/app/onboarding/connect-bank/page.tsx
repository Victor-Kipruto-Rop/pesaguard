import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingConnectBankPage() {
  return (
    <OnboardingLayout title="Connect your bank" step={5} total={10}>
      <div>
        <p className="muted">Connect your bank account for automated statement imports.</p>
        <div className="card-body">Integration options and connectors will appear here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/create-admin" next="/onboarding/connect-mpesa" />
    </OnboardingLayout>
  );
}
