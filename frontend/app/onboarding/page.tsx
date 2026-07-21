'use client';

import { useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

const STEPS = ['credentials', 'rules', 'notifications', 'sync'] as const;

export default function OnboardingPage() {
  const { t } = useLocale();
  const [step, setStep] = useState(0);
  const [done, setDone] = useState<boolean[]>([false, false, false, false]);

  const completeStep = () => {
    setDone((current) => {
      const next = [...current];
      next[step] = true;
      return next;
    });
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('onboardingPage.eyebrow')} title={t('onboardingPage.title')} summary={t('onboardingPage.summary')} />

      <div className="wizardSteps">
        {STEPS.map((key, index) => (
          <span key={key} className={`wizardStep ${index === step ? 'active' : ''} ${done[index] ? 'done' : ''}`}>
            {index + 1}. {t(`onboardingPage.steps.${key}`)}
          </span>
        ))}
      </div>

      <section className="card">
        {step === 0 && (
          <>
            <div className="sectionTitle">{t('onboardingPage.credentialsTitle')}</div>
            <p className="muted">{t('onboardingPage.credentialsBody')}</p>
            <div className="formGrid" style={{ maxWidth: 480, marginTop: 16 }}>
              <div className="formRow"><label>Consumer Key</label><input placeholder="Daraja consumer key" /></div>
              <div className="formRow"><label>Consumer Secret</label><input type="password" placeholder="Daraja consumer secret" /></div>
            </div>
          </>
        )}
        {step === 1 && (
          <>
            <div className="sectionTitle">{t('onboardingPage.rulesTitle')}</div>
            <p className="muted">{t('onboardingPage.rulesBody')}</p>
          </>
        )}
        {step === 2 && (
          <>
            <div className="sectionTitle">{t('onboardingPage.notificationsTitle')}</div>
            <p className="muted">{t('onboardingPage.notificationsBody')}</p>
            <a className="secondaryBtn" href="/notifications">{t('onboardingPage.openNotifications')}</a>
          </>
        )}
        {step === 3 && (
          <>
            <div className="sectionTitle">{t('onboardingPage.syncTitle')}</div>
            <p className="muted">{t('onboardingPage.syncBody')}</p>
          </>
        )}
        <div className="heroActions" style={{ marginTop: 20 }}>
          <button disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>{t('onboardingPage.back')}</button>
          <button onClick={completeStep}>{step === STEPS.length - 1 ? t('onboardingPage.finish') : t('onboardingPage.continue')}</button>
        </div>
      </section>
    </main>
  );
}
