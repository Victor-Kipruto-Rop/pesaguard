"use client";

import React, { useState } from 'react';
import { ArrowRight, LockKeyhole, Mail } from 'lucide-react';
import AuthPageShell from '../../../components/AuthPageShell';
// Using cookie-based auth; server sets HttpOnly cookies on /api/auth/login

export default function AuthLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        cache: 'no-store',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // server sets HttpOnly cookies; optionally returns tokens for local convenience
      window.location.href = '/notifications';
    } catch (err: any) {
      setError(err?.message ?? 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthPageShell
      eyebrow="Secure access"
      title="Welcome back"
      subtitle="Access your operational workspace and keep every critical workflow protected."
      footer={
        <p className="authPrompt">
          New to PesaGuard? <a href="/auth/register">Create account</a>
        </p>
      }
    >
      <form className="authForm" onSubmit={onSubmit}>
        <div className="authFormHeader">
          <h3>Sign in</h3>
          <p>Use your organization credentials to continue securely.</p>
        </div>

        <div className="authInputGroup">
          <label htmlFor="login-email">Email address</label>
          <input
            id="login-email"
            className="authInput"
            type="email"
            placeholder="name@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="authInputGroup">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            className="authInput"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="checkboxRow">
          <label className="authCheckbox">
            <input type="checkbox" defaultChecked />
            <span>Remember me</span>
          </label>
          <a href="/auth/forgot-password" className="authLink">Forgot password?</a>
        </div>

        {error ? <div className="error">{error}</div> : null}

        <button type="submit" className="authButton primary" disabled={loading}>
          <Mail size={18} /> {loading ? 'Signing in…' : 'Sign in'}
          <ArrowRight size={18} />
        </button>

        <button type="button" className="authButton secondary">
          <LockKeyhole size={18} /> Use SSO
        </button>
      </form>
    </AuthPageShell>
  );
}
