'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import PulseLine from '../../../components/PulseLine';
import { useLocale } from '../../../lib/i18n';

export default function SignupPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [form, setForm] = useState({ name: '', email: '', org: '', reason: '' });
  const [submitted, setSubmitted] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitted(true);
    window.setTimeout(() => router.push('/auth/login'), 2000);
  };

  return (
    <main className="authPage">
      <div className="authCard">
        <PulseLine height={32} />
        <p className="eyebrow">{t('auth.signupEyebrow')}</p>
        <h1>{t('auth.signupTitle')}</h1>
        <p className="muted">{t('auth.signupSummary')}</p>
        {submitted ? (
          <p className="muted">{t('auth.signupSubmitted')}</p>
        ) : (
          <form className="formGrid" onSubmit={submit}>
            <div className="formRow">
              <label htmlFor="name">{t('contact.name')}</label>
              <input id="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="formRow">
              <label htmlFor="email">{t('contact.email')}</label>
              <input id="email" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="formRow">
              <label htmlFor="org">{t('contact.org')}</label>
              <input id="org" required value={form.org} onChange={(e) => setForm({ ...form, org: e.target.value })} />
            </div>
            <div className="formRow">
              <label htmlFor="reason">{t('auth.signupReason')}</label>
              <textarea id="reason" rows={4} required value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
            </div>
            <button className="primaryBtn" type="submit">{t('auth.requestAccess')}</button>
          </form>
        )}
        <a href="/auth/login" className="muted">{t('auth.backToLogin')}</a>
      </div>
    </main>
  );
}
