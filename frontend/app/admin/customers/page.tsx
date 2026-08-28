'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';
import { adminFetch } from '../../../lib/adminApi';

interface TenantInfo {
  tenant_id: string;
  deployment_region?: string;
  backup_region?: string;
  log_region?: string;
  alert_channels?: string[];
  preferred_locale?: string;
  cross_border_transfer_allowed?: boolean;
}

export default function TenantCustomersPage() {
  const { t } = useLocale();
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadTenant = async () => {
      const response = await adminFetch<TenantInfo>('/admin/tenant/default');
      if (response.ok && response.data) {
        setTenant(response.data);
      } else if (response.status === 403) {
        setError('Admin access token is invalid. Please update it in Settings.');
      } else {
        setError('Unable to load tenant information.');
      }
    };

    void loadTenant();
  }, []);

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.customersEyebrow')} title={t('admin.customersTitle')} summary={t('admin.customersSummary')} />

      {error ? (
        <section className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </section>
      ) : null}

      <section className="card">
        <div className="sectionTitle">Tenant configuration</div>
        <div style={{ display: 'grid', gap: 12, marginTop: 16 }}>
          <div><strong>Tenant</strong>: {tenant?.tenant_id ?? 'default'}</div>
          <div><strong>Deployment region</strong>: {tenant?.deployment_region ?? 'ke-1'}</div>
          <div><strong>Backup region</strong>: {tenant?.backup_region ?? 'ke-1'}</div>
          <div><strong>Log region</strong>: {tenant?.log_region ?? 'ke-1'}</div>
          <div><strong>Alert channels</strong>: {(tenant?.alert_channels || ['slack']).join(', ')}</div>
          <div><strong>Locale</strong>: {tenant?.preferred_locale ?? 'en'}</div>
          <div><strong>Cross-border transfer</strong>: {tenant?.cross_border_transfer_allowed ? 'Enabled' : 'Disabled'}</div>
        </div>
      </section>
    </main>
  );
}
