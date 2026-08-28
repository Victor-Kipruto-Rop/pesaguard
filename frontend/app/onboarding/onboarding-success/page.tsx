import OnboardingLayout from '../../../components/OnboardingLayout';

export default function OnboardingOnboardingSuccessPage() {
  return (
    <OnboardingLayout title="Onboarding complete" step={10} total={10}>
      <div>
        <h2>All set — welcome aboard!</h2>
        <p className="muted">Your organization is configured. You can now access the dashboard and start reconciling.</p>
        <div className="card-body">
          <a href="/" className="btn primary">Go to Dashboard</a>
        </div>
      </div>
    </OnboardingLayout>
  );
}
