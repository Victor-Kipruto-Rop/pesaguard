'use client';

import { useEffect, useState } from 'react';
import { normalizeLocaleCandidate, useLocale } from '../../lib/i18n';

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

export default function SettingsPage() {
  const { t, locale, setLocale } = useLocale();
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
        const adminToken = window.localStorage.getItem('pesaguard.admin_token');
        // Prefer admin API when token is present
        if (adminToken) {
          const response = await fetch(`/admin/tenant/default`, { headers: { 'X-Admin-Token': adminToken } });
          if (response.ok) {
            const data = await response.json();
            setSettings(data);
            const nextLocale = normalizeLocaleCandidate(data.preferred_locale) ?? 'en';
            setLocale(nextLocale);
            return;
          }
        }

        // Fallback to public tenant endpoint
        const response = await fetch('/tenant/current');
        if (response.ok) {
          const data = await response.json();
          // map fields from public response into settings where possible
          setSettings((prev) => ({ ...prev, preferred_locale: data.preferred_locale }));
          const nextLocale = normalizeLocaleCandidate(data.preferred_locale) ?? 'en';
          setLocale(nextLocale);
        }
      } catch (err) {
        setError(t('settings.loadError') || 'Failed to load settings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadSettings();
  }, []);

  const save = async () => {
    try {
      const adminToken = window.localStorage.getItem('pesaguard.admin_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (adminToken) headers['X-Admin-Token'] = adminToken;

      const response = await fetch(`/admin/tenant/default`, {
        method: 'POST',
        headers,
        body: JSON.stringify(settings),
      });
      if (response.ok) {
        setSaved(true);
        const nextLocale = normalizeLocaleCandidate(settings.preferred_locale) ?? 'en';
        setLocale(nextLocale);
        setTimeout(() => setSaved(false), 3000);
      } else {
        setError(t('settings.saveError') || 'Failed to save settings');
      }
    } catch (err) {
      setError('Failed to save settings');
      console.error(err);
    }
  };

  const saveAdminToken = (token: string) => {
    try {
      window.localStorage.setItem('pesaguard.admin_token', token);
      // trigger reload of settings with admin privileges
      setLoading(true);
      setTimeout(() => window.location.reload(), 200);
    } catch (e) {
      console.error(e);
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
    transition: 'border-color 0.2s',
  } as const;

  return (
    <main className="shell">
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">Tenant Admin</p>
          <h1>{t('settings.title')}</h1>
          <p className="muted">{t('settings.subtitle')}</p>
        </div>
      </section>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted-color)' }}>
{t('settings.loading')}
        </div>
      ) : (
        <>
          <section className="card">
            <div className="sectionTitle">Admin Access</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <input
                placeholder="Admin token"
                defaultValue={typeof window !== 'undefined' ? window.localStorage.getItem('pesaguard.admin_token') || '' : ''}
                onBlur={(e) => saveAdminToken(e.currentTarget.value)}
                style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)', flex: 1 }}
              />
              <button onClick={() => { window.localStorage.removeItem('pesaguard.admin_token'); window.location.reload(); }} style={{ padding: '8px 12px', borderRadius: 8 }}>Clear</button>
            </div>
          </section>
          {error && (
            <section className="card" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid var(--danger)', borderRadius: '8px', padding: '12px 16px', color: 'var(--danger)', fontSize: '14px' }}>
              {error}
            </section>
          )}

          <section className="grid">
            <article className="card">
              <div className="sectionTitle">{t('settings.sections.localization')}</div>
              <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.preferredLocale')}
                  </label>
                  <select
                    value={settings.preferred_locale || 'en'}
                    onChange={(e) => setSettings({ ...settings, preferred_locale: e.target.value })}
                    style={inputStyle}
                  >
                    <option value="en">English</option>
                    <option value="sw">Kiswahili</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.deploymentRegion')}
                  </label>
                  <input
                    value={settings.deployment_region || ''}
                    onChange={(e) => setSettings({ ...settings, deployment_region: e.target.value })}
                    placeholder="ke-1"
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.backupRegion')}
                  </label>
                  <input
                    value={settings.backup_region || ''}
                    onChange={(e) => setSettings({ ...settings, backup_region: e.target.value })}
                    placeholder="ke-1"
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.logRegion')}
                  </label>
                  <input
                    value={settings.log_region || ''}
                    onChange={(e) => setSettings({ ...settings, log_region: e.target.value })}
                    placeholder="ke-1"
                    style={inputStyle}
                  />
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '13px', color: 'var(--muted-color)' }}>
                  <input
                    type="checkbox"
                    checked={!!settings.cross_border_transfer_allowed}
                    onChange={(e) => setSettings({ ...settings, cross_border_transfer_allowed: e.target.checked })}
                  />
                  {t('settings.sections.crossBorder')}
                </label>
              </div>
            </article>

            <article className="card">
              <div className="sectionTitle">{t('settings.sections.alertChannels')}</div>
              <div style={{ marginTop: 16 }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                  {t('settings.sections.alertChannelsLabel')}
                </label>
                <input
                  value={settings.alert_channels?.join(', ') || ''}
                  onChange={(e) => setSettings({ ...settings, alert_channels: e.target.value.split(',').map((item) => item.trim()) })}
                  placeholder="e.g., slack, email, webhook"
                  style={{
                    ...inputStyle,
                    onFocus: { borderColor: 'var(--accent)' },
                  } as any}
                />
                <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 6 }}>
                  {t('settings.sections.channelsHint')}
                </p>
              </div>
            </article>
          </section>

          <section className="grid">
            <article className="card">
              <div className="sectionTitle">{t('settings.sections.thresholds')}</div>
              <div style={{ display: 'grid', gap: 20, marginTop: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.warningThreshold')}
                  </label>
                  <input
                    type="number"
                    value={settings.thresholds?.warning || ''}
                    onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, warning: Number(e.target.value) } })}
                    placeholder="1000"
                    style={inputStyle}
                  />
                  <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 6 }}>
                    {t('settings.sections.warningThresholdHint')}
                  </p>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    {t('settings.sections.criticalThreshold')}
                  </label>
                  <input
                    type="number"
                    value={settings.thresholds?.critical || ''}
                    onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, critical: Number(e.target.value) } })}
                    placeholder="5000"
                    style={inputStyle}
                  />
                  <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 6 }}>
                    {t('settings.sections.criticalThresholdHint')}
                  </p>
                </div>
              </div>
            </article>

            <article className="card">
              <div className="sectionTitle">{t('settings.sections.slaPolicy')}</div>
              <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
                <div>
                  <span style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>{t('settings.sections.criticalResolutionWindow')}</span>
                  <strong style={{ fontSize: '18px', color: 'var(--accent)' }}>30 minutes</strong>
                </div>
                <div>
                  <span style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>{t('settings.sections.status')}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
                    <span style={{ color: '#10b981', fontSize: '14px', fontWeight: 500 }}>{t('settings.sections.active')}</span>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section style={{ display: 'grid', gap: 12 }}>
            <button
              onClick={save}
              style={{
                padding: '12px 20px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%)',
                border: 'none',
                color: 'white',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
              }}
              onMouseDown={(e) => {
                e.currentTarget.style.transform = 'scale(0.98)';
                e.currentTarget.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.2)';
              }}
              onMouseUp={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
              }}
            >
              {t('settings.save')}
            </button>

            {saved && (
              <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid #10b981', color: '#10b981', fontSize: '14px', textAlign: 'center' }}>
                {t('settings.saved')}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

