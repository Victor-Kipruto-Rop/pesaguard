import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingCreateAdminPage() {
  return (
    <OnboardingLayout title="Create administrator account" step={4} total={10}>
      <div>
        <p className="muted">Create the primary administrator who will manage the organization.</p>
        <form className="form-grid">
          <label>
            Full name
            <input name="adminName" />
          </label>
          <label>
            Email
            <input name="adminEmail" type="email" />
          </label>
        </form>
      </div>
      <OnboardingStepNav prev="/onboarding/organization-information" next="/onboarding/connect-bank" />
    </OnboardingLayout>
  );
}
