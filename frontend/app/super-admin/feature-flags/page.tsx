'use client';

import { useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const INITIAL_FLAGS = [
  { key: 'localized_alerts', label: 'Localized alerts', tenant: 'Pilot SACCO A', enabled: true },
  { key: 'auto_escalation', label: 'Auto escalation', tenant: 'Pilot SACCO A', enabled: true },
  { key: 'sandbox_mode', label: 'Sandbox mode', tenant: 'Pilot Fintech B', enabled: false },
];

export default function FeatureFlagsPage() {
  const { t } = useLocale();
  const [flags, setFlags] = useState(INITIAL_FLAGS);

  const toggle = (key: string) => {
    setFlags((current) => current.map((flag) => (flag.key === key ? { ...flag, enabled: !flag.enabled } : flag)));
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.flagsEyebrow')} title={t('admin.flagsTitle')} summary={t('admin.flagsSummary')} />
      <section className="card">
        <div className="tableWrap">
          <table>
            <thead><tr><th>{t('admin.feature')}</th><th>{t('admin.tenant')}</th><th>{t('admin.enabled')}</th><th>{t('dashboard.operations.table.action')}</th></tr></thead>
            <tbody>
              {flags.map((flag) => (
                <tr key={flag.key}>
                  <td>{flag.label}</td>
                  <td>{flag.tenant}</td>
                  <td><span className={`pill ${flag.enabled ? 'ok' : 'warning'}`}>{flag.enabled ? t('common.live') : t('common.draft')}</span></td>
                  <td><button onClick={() => toggle(flag.key)}>{flag.enabled ? t('admin.disable') : t('admin.enable')}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
