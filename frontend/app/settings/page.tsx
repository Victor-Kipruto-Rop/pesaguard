'use client';

import { useEffect, useState } from 'react';

interface TenantSettings {
  alert_channels?: string[];
  thresholds?: {
    warning?: number;
    critical?: number;
  };
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<TenantSettings>({ alert_channels: ['slack'], thresholds: { warning: 1000, critical: 5000 } });
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5001/tenants/default/settings');
        if (response.ok) {
          const data = await response.json();
          setSettings(data);
        }
      } catch (err) {
        setError('Failed to load settings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadSettings();
  }, []);

  const save = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/tenants/default/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        setError('Failed to save settings');
      }
    } catch (err) {
      setError('Failed to save settings');
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
    transition: 'border-color 0.2s',
  } as const;

  return (
    <main className="shell">
      <section className="hero">
        <div className="heroCopy">
          <p className="eyebrow">Tenant Admin</p>
          <h1>Settings and configuration</h1>
          <p className="muted">Manage alert channels, incident thresholds, and operational policies for your tenant.</p>
        </div>
      </section>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted-color)' }}>
          Loading settings...
        </div>
      ) : (
        <>
          {error && (
            <section className="card" style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid var(--danger)', borderRadius: '8px', padding: '12px 16px', color: 'var(--danger)', fontSize: '14px' }}>
              {error}
            </section>
          )}

          <section className="grid">
            <article className="card">
              <div className="sectionTitle">Alert channels</div>
              <div style={{ marginTop: 16 }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                  Active channels (comma-separated)
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
                  Configure where incident notifications are sent.
                </p>
              </div>
            </article>
          </section>

          <section className="grid">
            <article className="card">
              <div className="sectionTitle">Incident thresholds</div>
              <div style={{ display: 'grid', gap: 20, marginTop: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    Warning threshold (in units)
                  </label>
                  <input
                    type="number"
                    value={settings.thresholds?.warning || ''}
                    onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, warning: Number(e.target.value) } })}
                    placeholder="1000"
                    style={inputStyle}
                  />
                  <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 6 }}>
                    Discrepancies below this threshold trigger a warning.
                  </p>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 8, color: 'var(--muted-color)' }}>
                    Critical threshold (in units)
                  </label>
                  <input
                    type="number"
                    value={settings.thresholds?.critical || ''}
                    onChange={(e) => setSettings({ ...settings, thresholds: { ...settings.thresholds, critical: Number(e.target.value) } })}
                    placeholder="5000"
                    style={inputStyle}
                  />
                  <p style={{ fontSize: '12px', color: 'var(--muted-color)', marginTop: 6 }}>
                    Discrepancies above this threshold trigger a critical alert.
                  </p>
                </div>
              </div>
            </article>

            <article className="card">
              <div className="sectionTitle">SLA policy</div>
              <div style={{ display: 'grid', gap: 16, marginTop: 16 }}>
                <div>
                  <span style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>Critical resolution window</span>
                  <strong style={{ fontSize: '18px', color: 'var(--accent)' }}>30 minutes</strong>
                </div>
                <div>
                  <span style={{ display: 'block', fontSize: '13px', color: 'var(--muted-color)', marginBottom: 8 }}>Status</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
                    <span style={{ color: '#10b981', fontSize: '14px', fontWeight: 500 }}>Active</span>
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
              Save settings
            </button>

            {saved && (
              <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid #10b981', color: '#10b981', fontSize: '14px', textAlign: 'center' }}>
                ✓ Settings saved successfully
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

