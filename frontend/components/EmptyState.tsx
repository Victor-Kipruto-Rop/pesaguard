'use client';

interface EmptyStateProps {
  title: string;
  message: string;
  action?: React.ReactNode;
  icon?: string;
}

export default function EmptyState({ title, message, action, icon = '◌' }: EmptyStateProps) {
  return (
    <div className="emptyState emptyStateRich">
      <div className="emptyStateIcon" aria-hidden="true">{icon}</div>
      <h3>{title}</h3>
      <p className="muted">{message}</p>
      {action ? <div className="emptyStateAction">{action}</div> : null}
    </div>
  );
}
