import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingCreateOrganizationPage() {
  return (
    <OnboardingLayout title="Create your organization" step={2} total={10}>
      <form className="form-grid" action="#">
        <label>
          Organization name
          <input name="orgName" placeholder="Acme Corporation" />
        </label>
        <label>
          Website (optional)
          <input name="website" placeholder="https://example.com" />
        </label>
        <label>
          Time zone
          <select name="timezone">
            <option>UTC</option>
            <option>Africa/Nairobi</option>
            <option>Europe/London</option>
          </select>
        </label>
      </form>
      <OnboardingStepNav prev="/onboarding/welcome" next="/onboarding/organization-information" />
    </OnboardingLayout>
  );
}
