'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Documentation', href: '/super-admin/help-center/documentation', summary: 'Reference guides, operational playbooks and admin docs.' },
  { title: 'Support tickets', href: '/super-admin/help-center/support-tickets', summary: 'Track customer and operator support issues.' },
  { title: 'System status', href: '/super-admin/help-center/system-status', summary: 'Current service health and incident history.' },
  { title: 'Contact support', href: '/super-admin/help-center/contact-support', summary: 'Escalation and support routing information.' },
];

export default function AdminSupportPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Support"
      summary="Provide operators and admins with the support channels and resources they need."
      links={links}
    />
  );
}
