'use client';

import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

export default function AdminReconciliationPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <PageHeader
        eyebrow={t('admin.systemHealth')}
        title={t('admin.viewMonitoring')}
        summary={t('admin.systemHealthBody')}
      />
      <div className="card">
        <p className="muted">This placeholder page ensures the admin routes compile successfully.</p>
      </div>
    </main>
  );
}
