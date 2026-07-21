'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

interface NotificationSettings {
  alert_channels: string[];
  thresholds: { warning: number; critical: number };
  recipients: string;
}

export default function NotificationsPage() {
  const { t } = useLocale();
  const [settings, setSettings] = useState<NotificationSettings>({
    alert_channels: ['slack', 'email'],
    thresholds: { warning: 1000, critical: 5000 },
    recipients: 'finance-ops@tenant.example',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void fetch('/tenant/current')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.alert_channels) {
          setSettings((prev) => ({ ...prev, alert_channels: data.alert_channels }));
        }
      })
      .catch(() => undefined);
  }, []);

  const save = () => {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('notifications.eyebrow')} title={t('notifications.title')} summary={t('notifications.summary')} />

      <section className="grid twoUp">
        <article className="card">
          <div className="sectionTitle">{t('notifications.channelsTitle')}</div>
          <div className="formGrid">
            <div className="formRow">
              <label>{t('settings.sections.alertChannelsLabel')}</label>
              <input
                value={settings.alert_channels.join(', ')}
                onChange={(e) => setSettings({ ...settings, alert_channels: e.target.value.split(',').map((s) => s.trim()) })}
              />
            </div>
            <div className="formRow">
              <label>{t('notifications.recipients')}</label>
              <input value={settings.recipients} onChange={(e) => setSettings({ ...settings, recipients: e.target.value })} />
            </div>
          </div>
        </article>
        <article className="card">
          <div className="sectionTitle">{t('notifications.thresholdsTitle')}</div>
          <div className="formGrid">
            <div className="formRow">
              <label>{t('settings.sections.warningThreshold')}</label>
              <input type="number" value={settings.thresholds.warning} onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, warning: Number(e.target.value) } })} />
            </div>
            <div className="formRow">
              <label>{t('settings.sections.criticalThreshold')}</label>
              <input type="number" value={settings.thresholds.critical} onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, critical: Number(e.target.value) } })} />
            </div>
          </div>
        </article>
      </section>

      <button className="primaryBtn" onClick={save}>{t('settings.save')}</button>
      {saved ? <div className="toast">{t('settings.saved')}</div> : null}
    </main>
  );
}
