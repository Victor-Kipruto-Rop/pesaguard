'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Customer list', href: '/super-admin/customers/customer-list', summary: 'Directory of customers, tenants and counterparties.' },
  { title: 'Customer details', href: '/super-admin/customers/customer-details', summary: 'Profile and account-level details.' },
  { title: 'Customer accounts', href: '/super-admin/customers/customer-accounts', summary: 'Linked accounts and wallet relationships.' },
  { title: 'Customer activity', href: '/super-admin/customers/customer-activity', summary: 'Behavioral and transactional activity trends.' },
  { title: 'Customer risk', href: '/super-admin/customers/customer-risk', summary: 'Risk scoring and exposure assessment.' },
  { title: 'Customer verification', href: '/super-admin/customers/customer-verification', summary: 'KYC and verification workflow state.' },
  { title: 'Customer documents', href: '/super-admin/customers/customer-documents', summary: 'Uploaded documents and evidence files.' },
];

export default function AdminCustomersPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Customers"
      summary="Manage customer records, accounts, verification status and risk posture."
      links={links}
    />
  );
}
