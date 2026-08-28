'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'General settings', href: '/super-admin/settings/general-settings', summary: 'Core platform configuration and defaults.' },
  { title: 'Organization settings', href: '/super-admin/settings/organization-settings', summary: 'Tenant and organization-level settings.' },
  { title: 'Branding', href: '/super-admin/settings/branding', summary: 'Visual identity, logos and front-end themes.' },
  { title: 'Currency', href: '/super-admin/settings/currency', summary: 'Currency and settlement preferences.' },
  { title: 'Time zone', href: '/super-admin/settings/time-zone', summary: 'Regional date and timezone configuration.' },
  { title: 'Taxes', href: '/super-admin/settings/taxes', summary: 'Tax rules and compliance configuration.' },
  { title: 'Business rules', href: '/super-admin/settings/business-rules', summary: 'Operational policy and decision rules.' },
  { title: 'Automation rules', href: '/super-admin/settings/automation-rules', summary: 'Rule-driven automation and orchestration.' },
];

export default function AdminSettingsPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Settings"
      summary="Configure core platform behavior, enterprise policy, and tenant preferences."
      links={links}
    />
  );
}
