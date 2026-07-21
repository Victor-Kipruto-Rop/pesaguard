'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PulseLine from '../../../components/PulseLine';
import { useLocale } from '../../../lib/i18n';

export default function ResetPasswordPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (password !== confirm) {
      setError(t('auth.passwordMismatch'));
      return;
    }
    router.push('/auth/login');
  };

  return (
    <main className="authPage">
      <div className="authCard">
        <PulseLine height={32} />
        <p className="eyebrow">{t('auth.resetEyebrow')}</p>
        <h1>{t('auth.resetTitle')}</h1>
        <p className="muted">{t('auth.resetSummary')}</p>
        <form className="formGrid" onSubmit={submit}>
          <div className="formRow">
            <label htmlFor="password">{t('auth.newPassword')}</label>
            <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="formRow">
            <label htmlFor="confirm">{t('auth.confirmPassword')}</label>
            <input id="confirm" type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
          {error ? <div className="pill danger">{error}</div> : null}
          <button className="primaryBtn" type="submit">{t('auth.updatePassword')}</button>
        </form>
      </div>
    </main>
  );
}
