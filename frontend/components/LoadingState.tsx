'use client';

import PulseLine from './PulseLine';

interface LoadingStateProps {
  message?: string;
}

export default function LoadingState({ message = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="loadingState" role="status" aria-live="polite">
      <PulseLine height={36} />
      <p className="muted">{message}</p>
    </div>
  );
}
