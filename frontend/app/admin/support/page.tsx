'use client';

import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const TICKETS = [
  { id: 'PG-104', tenant: 'Pilot SACCO A', subject: 'Webhook delay during peak hour', priority: 'High', status: 'Open' },
  { id: 'PG-103', tenant: 'Pilot Fintech B', subject: 'Need Kiswahili SMS template review', priority: 'Medium', status: 'In progress' },
];

export default function AdminSupportPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.supportEyebrow')} title={t('admin.supportTitle')} summary={t('admin.supportSummary')} />
      <section className="card">
        <div className="tableWrap">
          <table>
            <thead><tr><th>ID</th><th>{t('admin.tenant')}</th><th>{t('admin.subject')}</th><th>{t('admin.priority')}</th><th>{t('dashboard.operations.table.status')}</th></tr></thead>
            <tbody>
              {TICKETS.map((ticket) => (
                <tr key={ticket.id}>
                  <td className="mono">{ticket.id}</td>
                  <td>{ticket.tenant}</td>
                  <td>{ticket.subject}</td>
                  <td><span className={`pill ${ticket.priority === 'High' ? 'danger' : 'warning'}`}>{ticket.priority}</span></td>
                  <td>{ticket.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
