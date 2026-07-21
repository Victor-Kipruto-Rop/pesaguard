'use client';

import PageHeader from '../../../components/PageHeader';
import { useLocale } from '../../../lib/i18n';

const FUNNEL = [
  { tenant: 'Pilot SACCO A', step: 'Live', progress: 100, stuck: false },
  { tenant: 'Pilot Fintech B', step: 'Credentials', progress: 35, stuck: true },
];

export default function PilotStatusPage() {
  const { t } = useLocale();

  return (
    <main className="shell">
      <PageHeader eyebrow={t('pilotStatus.eyebrow')} title={t('pilotStatus.title')} summary={t('pilotStatus.summary')} />
      <section className="card">
        <div className="tableWrap">
          <table>
            <thead><tr><th>{t('admin.tenant')}</th><th>{t('pilotStatus.currentStep')}</th><th>{t('pilotStatus.progress')}</th><th>{t('admin.flags')}</th></tr></thead>
            <tbody>
              {FUNNEL.map((row) => (
                <tr key={row.tenant}>
                  <td>{row.tenant}</td>
                  <td>{row.step}</td>
                  <td><span className="mono">{row.progress}%</span></td>
                  <td>{row.stuck ? <span className="pill danger">{t('admin.stuck')}</span> : <span className="pill ok">{t('pilotStatus.onTrack')}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
