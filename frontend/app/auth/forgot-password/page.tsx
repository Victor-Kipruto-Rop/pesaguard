'use client';

import { useState } from 'react';
import PulseLine from '../../../components/PulseLine';
import { useLocale } from '../../../lib/i18n';

export default function ForgotPasswordPage() {
  const { t } = useLocale();
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setSent(true);
  };

  return (
    <main className="authPage">
      <div className="authCard">
        <PulseLine height={32} />
        <p className="eyebrow">{t('auth.forgotEyebrow')}</p>
        <h1>{t('auth.forgotTitle')}</h1>
        <p className="muted">{t('auth.forgotSummary')}</p>
        {sent ? (
          <p className="muted">{t('auth.forgotSent')}</p>
        ) : (
          <form className="formGrid" onSubmit={submit}>
            <div className="formRow">
              <label htmlFor="email">{t('loginPage.email')}</label>
              <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="primaryBtn" type="submit">{t('auth.sendReset')}</button>
          </form>
        )}
        <a href="/auth/login" className="muted">{t('auth.backToLogin')}</a>
      </div>
    </main>
  );
}
