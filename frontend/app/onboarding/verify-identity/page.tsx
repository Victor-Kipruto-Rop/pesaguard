import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingVerifyIdentityPage() {
  return (
    <OnboardingLayout title="Verify identity" step={9} total={10}>
      <div>
        <p className="muted">Verify organization and admin identity using uploaded documents.</p>
        <div className="card-body">Verification status and instructions will be shown here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/upload-documents" next="/onboarding/complete-setup" />
    </OnboardingLayout>
  );
}
