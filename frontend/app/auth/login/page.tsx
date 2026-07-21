'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PulseLine from '../../../components/PulseLine';
import { useLocale } from '../../../lib/i18n';

export default function LoginPage() {
  const router = useRouter();
  const { t } = useLocale();
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
    setError(t('loginPage.invalidCredentials'));
  };

  return (
    <main className="authPage">
      <div className="authCard">
        <PulseLine height={32} />
        <p className="eyebrow">{t('loginPage.badge')}</p>
        <h1>{t('loginPage.title')}</h1>
        <p className="muted">{t('loginPage.summary')}</p>

        <form className="formGrid" onSubmit={submit}>
          <div className="formRow">
            <label htmlFor="email">{t('loginPage.email')}</label>
            <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('loginPage.emailPlaceholder')} />
          </div>
          <div className="formRow">
            <label htmlFor="password">{t('loginPage.password')}</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('loginPage.passwordPlaceholder')} />
          </div>
          {error ? <div className="pill danger">{error}</div> : null}
          <button className="primaryBtn" type="submit">{t('loginPage.signIn')}</button>
        </form>

        <div className="authLinks">
          <a href="/auth/forgot-password">{t('auth.forgotPassword')}</a>
          <a href="/auth/signup">{t('auth.requestAccess')}</a>
        </div>

        <p className="muted small">{t('loginPage.demoHint')} <span className="mono">ops@pesaguard.io / demo123</span></p>
      </div>
    </main>
  );
}
