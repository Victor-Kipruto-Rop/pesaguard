'use client';

import { useLocale } from '../lib/i18n';

export default function OnboardingLinks() {
  const { locale, t } = useLocale();
  const docLocale = locale === 'sw' ? 'sw' : 'en';

  return (
    <section className="panel">
      <h2>{t('onboarding.title')}</h2>
      <p className="muted">{t('onboarding.subtitle')}</p>
      <div className="downloadRow" style={{ marginTop: 16 }}>
        <a className="primaryBtn" href={`/docs/customer/GETTING_STARTED_${docLocale}.md`} target="_blank" rel="noreferrer">
          {t('onboarding.gettingStarted')}
        </a>
        <a className="secondaryBtn" href={`/docs/customer/FAQ_${docLocale}.md`} target="_blank" rel="noreferrer">
          {t('onboarding.faq')}
        </a>
      </div>
    </section>
  );
}
