'use client';

import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const ENTRIES = [
  { action: 'Support access granted', actor: 'pesaguard.support', time: '2026-07-14 09:12', detail: 'Read-only tenant settings review' },
  { action: 'Threshold updated', actor: 'pesaguard.ops', time: '2026-07-13 16:40', detail: 'Critical threshold set to 5000 for Pilot SACCO A' },
  { action: 'Feature flag toggled', actor: 'pesaguard.ops', time: '2026-07-12 11:05', detail: 'Enabled localized alerts for Pilot SACCO A' },
];

export default function AdminAuditLogPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.internalAuditEyebrow')} title={t('admin.internalAuditTitle')} summary={t('admin.internalAuditSummary')} />
      <section className="card">
        <div className="tableWrap">
          <table>
            <thead><tr><th>{t('auditLog.action')}</th><th>{t('auditLog.actor')}</th><th>{t('auditLog.time')}</th><th>{t('auditLog.detail')}</th></tr></thead>
            <tbody>
              {ENTRIES.map((entry) => (
                <tr key={entry.time + entry.action}><td>{entry.action}</td><td>{entry.actor}</td><td className="mono">{entry.time}</td><td>{entry.detail}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
