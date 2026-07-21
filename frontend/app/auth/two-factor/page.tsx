'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PulseLine from '../../../components/PulseLine';
import { useLocale } from '../../../lib/i18n';

export default function TwoFactorPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [code, setCode] = useState('');

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (code.length >= 6) {
      localStorage.setItem('pesaguard.auth', 'true');
      router.push('/');
    }
  };

  return (
    <main className="authPage">
      <div className="authCard">
        <PulseLine height={32} />
        <p className="eyebrow">{t('auth.twoFactorEyebrow')}</p>
        <h1>{t('auth.twoFactorTitle')}</h1>
        <p className="muted">{t('auth.twoFactorSummary')}</p>
        <form className="formGrid" onSubmit={submit}>
          <div className="formRow">
            <label htmlFor="code">{t('auth.verificationCode')}</label>
            <input id="code" className="mono" inputMode="numeric" maxLength={6} required value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} />
          </div>
          <button className="primaryBtn" type="submit">{t('auth.verify')}</button>
        </form>
      </div>
    </main>
  );
}
