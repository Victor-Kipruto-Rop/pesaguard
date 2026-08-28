'use client';

import { useEffect, useState } from 'react';
import PageHeader from '../../../components/PageHeader';
import { normalizeLocaleCandidate, useLocale } from '../../../lib/i18n';
import { adminFetch } from '../../../lib/adminApi';

interface TenantSettings {
  alert_channels?: string[];
  thresholds?: {
    warning?: number;
    critical?: number;
  };
  preferred_locale?: string;
  deployment_region?: string;
  backup_region?: string;
  log_region?: string;
  cross_border_transfer_allowed?: boolean;
}

export default function TenantAdminSettingsPage() {
  const { t, setLocale } = useLocale();
  const [settings, setSettings] = useState<TenantSettings>({
    alert_channels: ['slack'],
    thresholds: { warning: 1000, critical: 5000 },
    preferred_locale: 'en',
    deployment_region: 'ke-1',
    backup_region: 'ke-1',
    log_region: 'ke-1',
    cross_border_transfer_allowed: false,
  });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await adminFetch<TenantSettings>('/admin/tenant/default');
        if (response.ok && response.data) {
          setSettings(response.data);
          const nextLocale = normalizeLocaleCandidate(response.data.preferred_locale) ?? 'en';
          setLocale(nextLocale);
          setError('');
          return;
        }

        if (response.status === 403) {
          setError('Admin token is invalid. Please update it in Settings.');
          return;
        }

        setError('Failed to load tenant settings.');
      } catch (err) {
        setError('Failed to load tenant settings.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    void loadSettings();
  }, [setLocale]);

  const save = async () => {
    try {
      const response = await adminFetch<TenantSettings>('/admin/tenant/default', {
        method: 'POST',
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setSaved(true);
        const nextLocale = normalizeLocaleCandidate(settings.preferred_locale) ?? 'en';
        setLocale(nextLocale);
        setTimeout(() => setSaved(false), 3000);
        setError('');
        return;
      }

      if (response.status === 403) {
        setError('Admin token is invalid. Please update it in Settings.');
        return;
      }

      setError('Failed to save tenant settings.');
    } catch (err) {
      setError('Failed to save tenant settings.');
      console.error(err);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '8px',
    border: '1px solid var(--border)',
    background: 'var(--input-bg)',
    color: 'white',
    fontSize: '14px',
  } as const;

  return (
    <main className="shell">
      <PageHeader eyebrow={t('admin.customersEyebrow')} title={t('admin.settingsTitle')} summary={t('admin.settingsSummary')} />

      {loading ? (
        <section className="card">
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted-color)' }}>Loading tenant settings…</div>
        </section>
      ) : (
        <>
          {error ? (
            <section className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
              <p style={{ color: '#ef4444' }}>{error}</p>
            </section>
          ) : null}

          <section className="grid">
            <article className="card">
              <div className="sectionTitle">Tenant preferences</div>
              <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--muted-color)' }}>
                  Preferred locale
                  <select value={settings.preferred_locale || 'en'} onChange={(e) => setSettings({ ...settings, preferred_locale: e.target.value })} style={inputStyle}>
                    <option value="en">English</option>
                    <option value="sw">Kiswahili</option>
                  </select>
                </label>

                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--muted-color)' }}>
                  Alert channels
                  <input value={settings.alert_channels?.join(', ') || ''} onChange={(e) => setSettings({ ...settings, alert_channels: e.target.value.split(',').map((item) => item.trim()) })} placeholder="slack, email" style={inputStyle} />
                </label>
              </div>
            </article>

            <article className="card">
              <div className="sectionTitle">Deployment details</div>
              <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--muted-color)' }}>
                  Deployment region
                  <input value={settings.deployment_region || ''} onChange={(e) => setSettings({ ...settings, deployment_region: e.target.value })} placeholder="ke-1" style={inputStyle} />
                </label>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--muted-color)' }}>
                  Backup region
                  <input value={settings.backup_region || ''} onChange={(e) => setSettings({ ...settings, backup_region: e.target.value })} placeholder="ke-1" style={inputStyle} />
                </label>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--muted-color)' }}>
                  Log region
                  <input value={settings.log_region || ''} onChange={(e) => setSettings({ ...settings, log_region: e.target.value })} placeholder="ke-1" style={inputStyle} />
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--muted-color)' }}>
                  <input type="checkbox" checked={!!settings.cross_border_transfer_allowed} onChange={(e) => setSettings({ ...settings, cross_border_transfer_allowed: e.target.checked })} />
                  Cross-border transfer allowed
                </label>
              </div>
            </article>
          </section>

          <section className="card" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button className="primaryBtn" type="button" onClick={save}>
              {saved ? 'Saved' : 'Save tenant settings'}
            </button>
          </section>
        </>
      )}
    </main>
  );
}
