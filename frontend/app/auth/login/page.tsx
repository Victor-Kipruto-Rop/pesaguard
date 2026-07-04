'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('ops@pesaguard.io');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (email && password) {
      localStorage.setItem('pesaguard.auth', 'true');
      router.push('/');
      return;
    }
    setError('Please enter a valid email and password.');
  };

  return (
    <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '20px', background: 'linear-gradient(135deg, var(--bg) 0%, var(--bg-secondary) 100%)' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ marginBottom: 40, textAlign: 'center' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--accent)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            PesaGuard Control Center
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: 12, color: 'white' }}>Access control</h1>
          <p style={{ fontSize: '14px', color: 'var(--muted-color)', lineHeight: 1.6 }}>
            Secure demo authentication. Production auth layer can be integrated later.
          </p>
        </div>

        <form onSubmit={submit} style={{ display: 'grid', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 6, color: 'var(--muted-color)' }}>Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ops@pesaguard.io"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--input-bg)',
                color: 'white',
                fontSize: '14px',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
              onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: 6, color: 'var(--muted-color)' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                background: 'var(--input-bg)',
                color: 'white',
                fontSize: '14px',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--accent)')}
              onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
            />
          </div>

          {error && (
            <div style={{ padding: '10px 12px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', color: 'var(--danger)', fontSize: '13px' }}>
              {error}
            </div>
          )}

          <button
            className="primaryBtn"
            type="submit"
            style={{
              marginTop: 6,
              padding: '12px 16px',
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
            Sign in
          </button>
        </form>

        <div style={{ marginTop: 24, padding: '12px', borderRadius: '6px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '13px', color: 'var(--muted-color)', textAlign: 'center' }}>
          Demo credentials: <strong style={{ color: 'var(--accent)' }}>ops@pesaguard.io</strong> / <strong style={{ color: 'var(--accent)' }}>demo123</strong>
        </div>
      </div>
    </main>
  );
}

