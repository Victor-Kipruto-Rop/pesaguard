'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Audit trail', href: '/super-admin/audit-compliance/audit-trail', summary: 'Operational and governance audit history.' },
  { title: 'Compliance reports', href: '/super-admin/audit-compliance/compliance-reports', summary: 'Policy and regulation compliance reporting.' },
  { title: 'Regulatory reports', href: '/super-admin/audit-compliance/regulatory-reports', summary: 'Sector-specific reporting output.' },
  { title: 'Consent management', href: '/super-admin/audit-compliance/consent-management', summary: 'Consent and privacy policy records.' },
  { title: 'Access logs', href: '/super-admin/audit-compliance/access-logs', summary: 'User and service access event history.' },
];

export default function AdminAuditCompliancePage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Audit & Compliance"
      summary="Sustain governance visibility, evidence trails and compliance readiness."
      links={links}
    />
  );
}
