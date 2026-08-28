import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingCompleteSetupPage() {
  return (
    <OnboardingLayout title="Complete setup" step={10} total={10}>
      <div>
        <p className="muted">You're almost done — finalize settings and review configuration.</p>
        <div className="card-body">Review summary and finish button will be here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/verify-identity" next="/onboarding/onboarding-success" />
    </OnboardingLayout>
  );
}
