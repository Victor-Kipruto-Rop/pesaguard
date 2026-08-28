'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Daily reports', href: '/super-admin/reports/daily-reports', summary: 'Daily operational and settlement snapshots.' },
  { title: 'Weekly reports', href: '/super-admin/reports/weekly-reports', summary: 'Short-term business and performance insights.' },
  { title: 'Monthly reports', href: '/super-admin/reports/monthly-reports', summary: 'Month-end oversight and planning reports.' },
  { title: 'Annual reports', href: '/super-admin/reports/annual-reports', summary: 'Yearly governance and strategic review packs.' },
  { title: 'Finance reports', href: '/super-admin/reports/financial-reports', summary: 'Revenue, liquidity and settlement reporting.' },
  { title: 'Audit reports', href: '/super-admin/reports/audit-reports', summary: 'Control and compliance review outputs.' },
  { title: 'Export center', href: '/super-admin/reports/export-center', summary: 'Manage exports for reporting and analytics.' },
];

export default function AdminReportsPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Reports"
      summary="Deliver governance-ready reporting for daily operations, finance and audit."
      links={links}
    />
  );
}
