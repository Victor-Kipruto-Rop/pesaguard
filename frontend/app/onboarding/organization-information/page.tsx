import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingOrganizationInformationPage() {
  return (
    <OnboardingLayout title="Organization information" step={3} total={10}>
      <div>
        <p className="muted">Enter business details used for compliance and reporting.</p>
        <form className="form-grid">
          <label>
            Registration number
            <input name="regNumber" />
          </label>
          <label>
            Legal form
            <input name="legalForm" />
          </label>
        </form>
      </div>
      <OnboardingStepNav prev="/onboarding/create-organization" next="/onboarding/create-admin" />
    </OnboardingLayout>
  );
}
