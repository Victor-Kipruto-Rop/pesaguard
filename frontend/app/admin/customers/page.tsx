'use client';

import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const CUSTOMERS = [
  { name: 'Pilot SACCO A', plan: 'Pilot', onboarding: 'Live', health: 'Healthy', stuck: false },
  { name: 'Pilot Fintech B', plan: 'Pilot', onboarding: 'Credentials', health: 'Setup', stuck: true },
];

export default function AdminCustomersPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.customersEyebrow')} title={t('admin.customersTitle')} summary={t('admin.customersSummary')} />
      <section className="card">
        <div className="tableWrap">
          <table>
            <thead><tr><th>{t('contact.org')}</th><th>{t('admin.plan')}</th><th>{t('admin.onboarding')}</th><th>{t('admin.accountHealth')}</th><th>{t('admin.flags')}</th></tr></thead>
            <tbody>
              {CUSTOMERS.map((customer) => (
                <tr key={customer.name}>
                  <td>{customer.name}</td>
                  <td>{customer.plan}</td>
                  <td>{customer.onboarding}</td>
                  <td><span className={`pill ${customer.health === 'Healthy' ? 'ok' : 'warning'}`}>{customer.health}</span></td>
                  <td>{customer.stuck ? <span className="pill danger">{t('admin.stuck')}</span> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
