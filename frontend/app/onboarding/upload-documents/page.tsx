import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingUploadDocumentsPage() {
  return (
    <OnboardingLayout title="Upload documents" step={8} total={10}>
      <div>
        <p className="muted">Upload KYC and legal documents for compliance checks.</p>
        <div className="card-body">Drag-and-drop uploader and status list will be here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/invite-team" next="/onboarding/verify-identity" />
    </OnboardingLayout>
  );
}
