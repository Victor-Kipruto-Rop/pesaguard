'use client';

import { useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

export default function FeedbackPage() {
  const { t } = useLocale();
  const [message, setMessage] = useState('');
  const [category, setCategory] = useState('issue');
  const [sent, setSent] = useState(false);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setSent(true);
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('feedback.eyebrow')} title={t('feedback.title')} summary={t('feedback.summary')} />
      <section className="card">
        {sent ? (
          <p className="muted">{t('feedback.sent')}</p>
        ) : (
          <form className="formGrid" onSubmit={submit}>
            <div className="formRow">
              <label>{t('feedback.category')}</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="issue">{t('feedback.issue')}</option>
                <option value="feature">{t('feedback.feature')}</option>
                <option value="question">{t('feedback.question')}</option>
              </select>
            </div>
            <div className="formRow">
              <label>{t('contact.message')}</label>
              <textarea rows={6} required value={message} onChange={(e) => setMessage(e.target.value)} />
            </div>
            <button className="primaryBtn" type="submit">{t('feedback.submit')}</button>
          </form>
        )}
      </section>
    </main>
  );
}
