import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingInviteTeamPage() {
  return (
    <OnboardingLayout title="Invite your team" step={7} total={10}>
      <div>
        <p className="muted">Invite teammates and set roles to delegate access.</p>
        <div className="card-body">Invite form and role selector will appear here.</div>
      </div>
      <OnboardingStepNav prev="/onboarding/connect-mpesa" next="/onboarding/upload-documents" />
    </OnboardingLayout>
  );
}
