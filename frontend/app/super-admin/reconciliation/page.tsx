'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Reconciliation dashboard', href: '/super-admin/reconciliation/reconciliation-dashboard', summary: 'High-level balance and match health.' },
  { title: 'Daily reconciliation', href: '/super-admin/reconciliation/daily-reconciliation', summary: 'Daily match and settlement tasks.' },
  { title: 'Automatic reconciliation', href: '/super-admin/reconciliation/automatic-reconciliation', summary: 'Rule-driven reconciliation automation.' },
  { title: 'Manual reconciliation', href: '/super-admin/reconciliation/manual-reconciliation', summary: 'Analyst review and exception handling.' },
  { title: 'Unmatched transactions', href: '/super-admin/reconciliation/unmatched-transactions', summary: 'Pairs without a valid counterpart.' },
  { title: 'Matched transactions', href: '/super-admin/reconciliation/matched-transactions', summary: 'Successfully matched records.' },
  { title: 'Partial matches', href: '/super-admin/reconciliation/partial-matches', summary: 'Near-matches that need follow-up.' },
  { title: 'Approval queue', href: '/super-admin/reconciliation/approval-queue', summary: 'Pending approvals for reconciliation actions.' },
];

export default function AdminReconciliationPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Reconciliation"
      summary="Coordinate match policies, manual reviews and reconciliation workflows."
      links={links}
    />
  );
}
