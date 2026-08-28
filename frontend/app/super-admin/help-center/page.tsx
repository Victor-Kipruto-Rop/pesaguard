'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Documentation', href: '/super-admin/help-center/documentation', summary: 'Reference guides and operating manuals.' },
  { title: 'Tutorials', href: '/super-admin/help-center/tutorials', summary: 'Onboarding and feature walkthroughs.' },
  { title: 'FAQs', href: '/super-admin/help-center/faqs', summary: 'Common operator and customer questions.' },
  { title: 'Contact support', href: '/super-admin/help-center/contact-support', summary: 'Support routing and escalation details.' },
  { title: 'Support tickets', href: '/super-admin/help-center/support-tickets', summary: 'Case tracking and follow-up status.' },
  { title: 'System status', href: '/super-admin/help-center/system-status', summary: 'Service health and incident communications.' },
];

export default function AdminHelpCenterPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Help Center"
      summary="Provide support material, guidance and escalations for operators and clients."
      links={links}
    />
  );
}
