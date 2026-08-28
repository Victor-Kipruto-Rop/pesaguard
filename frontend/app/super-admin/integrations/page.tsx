'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'M-Pesa', href: '/super-admin/integrations/mpesa', summary: 'Mobile money integration status and channels.' },
  { title: 'Banks', href: '/super-admin/integrations/banks', summary: 'Banking partner connections and routing.' },
  { title: 'ERP systems', href: '/super-admin/integrations/erp-systems', summary: 'ERP and enterprise system connectors.' },
  { title: 'Accounting systems', href: '/super-admin/integrations/accounting-systems', summary: 'Ledger and finance system integrations.' },
  { title: 'Payment gateways', href: '/super-admin/integrations/payment-gateways', summary: 'External gateway and switch connectivity.' },
  { title: 'APIs', href: '/super-admin/integrations/apis', summary: 'Internal and partner API registry.' },
  { title: 'Webhooks', href: '/super-admin/integrations/webhooks', summary: 'Webhook configuration and delivery status.' },
];

export default function AdminIntegrationsPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Integrations"
      summary="Manage connector health, partner integrations and downstream systems."
      links={links}
    />
  );
}
