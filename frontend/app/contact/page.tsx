'use client';

import { useState } from 'react';
import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

export default function ContactPage() {
  const { t } = useLocale();
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', org: '', message: '' });

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setSent(true);
  };

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('contact.eyebrow')} title={t('contact.title')} summary={t('contact.summary')} />

      <section className="grid twoUp">
        <article className="card">
          <div className="sectionTitle">{t('contact.formTitle')}</div>
          {sent ? (
            <p className="muted">{t('contact.sent')}</p>
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
                <input id="org" value={form.org} onChange={(e) => setForm({ ...form, org: e.target.value })} />
              </div>
              <div className="formRow">
                <label htmlFor="message">{t('contact.message')}</label>
                <textarea id="message" rows={5} required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
              </div>
              <button className="primaryBtn" type="submit">{t('contact.submit')}</button>
            </form>
          )}
        </article>
        <article className="card">
          <div className="sectionTitle">{t('contact.altTitle')}</div>
          <p className="muted">{t('contact.altBody')}</p>
          <a className="secondaryBtn" href="mailto:pilot-support@pesaguard.example">{t('contact.emailUs')}</a>
        </article>
      </section>
    </main>
  );
}
