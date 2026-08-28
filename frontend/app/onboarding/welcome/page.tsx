import OnboardingLayout from '../../../components/OnboardingLayout';
import OnboardingStepNav from '../../../components/OnboardingStepNav';

export default function OnboardingWelcomePage() {
  return (
    <OnboardingLayout title="Welcome to PesaGuard" step={1} total={10}>
      <div className="welcome-hero">
        <p className="lead">Welcome! Let's get your organization set up. The guided setup only takes a few minutes.</p>
        <ul className="features">
          <li><strong>Secure</strong> by default — cookie-based sessions and enterprise controls.</li>
          <li><strong>Connected</strong> — integrate with M-Pesa, banks and webhooks.</li>
          <li><strong>Actionable</strong> — alerts and reconciliation pipelines configured for you.</li>
        </ul>
      </div>
      <OnboardingStepNav next="/onboarding/create-organization" />
    </OnboardingLayout>
  );
}
