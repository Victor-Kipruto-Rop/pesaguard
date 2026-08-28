'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'All transactions', href: '/super-admin/transactions/transactions', summary: 'Unified ledger and payment transaction oversight.' },
  { title: 'Pending transactions', href: '/super-admin/transactions/pending-transactions', summary: 'Items awaiting processing or analyst intervention.' },
  { title: 'Successful transactions', href: '/super-admin/transactions/successful-transactions', summary: 'Completed payment outcomes and settlement state.' },
  { title: 'Failed transactions', href: '/super-admin/transactions/failed-transactions', summary: 'Rejected or errored payment attempts.' },
  { title: 'Duplicate transactions', href: '/super-admin/transactions/duplicate-transactions', summary: 'Potential duplicate records and repeat transfers.' },
  { title: 'Suspicious transactions', href: '/super-admin/transactions/suspicious-transactions', summary: 'Flagged items requiring extra scrutiny.' },
  { title: 'High-value transactions', href: '/super-admin/transactions/high-value-transactions', summary: 'Large payment events with elevated controls.' },
  { title: 'Transaction details', href: '/super-admin/transactions/transaction-details', summary: 'Detailed drill-downs for a specific transaction.' },
];

export default function AdminTransactionsPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Transactions"
      summary="Monitor and govern payment activity across the full transaction lifecycle."
      links={links}
    />
  );
}
