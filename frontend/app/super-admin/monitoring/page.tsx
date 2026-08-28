'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Live system status', href: '/super-admin/monitoring/live-system-status', summary: 'Current health and status across services.' },
  { title: 'Queue monitor', href: '/super-admin/monitoring/queue-monitor', summary: 'Background job and queue depth visibility.' },
  { title: 'API monitor', href: '/super-admin/monitoring/api-monitor', summary: 'API throughput, errors and latency.' },
  { title: 'Database monitor', href: '/super-admin/monitoring/database-monitor', summary: 'Database health and replication status.' },
  { title: 'Server monitor', href: '/super-admin/monitoring/server-monitor', summary: 'Host and infrastructure performance metrics.' },
  { title: 'Logs', href: '/super-admin/monitoring/logs', summary: 'System logs and diagnostic events.' },
  { title: 'Error tracking', href: '/super-admin/monitoring/error-tracking', summary: 'Application error trends and incidents.' },
];

export default function AdminMonitoringPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Monitoring"
      summary="Observe system runtime, performance, and health signals in real time."
      links={links}
    />
  );
}
