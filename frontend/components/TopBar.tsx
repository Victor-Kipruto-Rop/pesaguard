'use client';

import ThemeToggle from './ThemeToggle';
import LocaleSwitcher from './LocaleSwitcher';
import { useLocale } from '../lib/i18n';

export default function TopBar() {
  const { t } = useLocale();

  return (
    <div className="topbar">
      <div className="brandBlock">
        <div className="brandMark">PG</div>
        <div>
          <div className="brand">{t('brand.name')}</div>
          <div className="brandSub">{t('brand.subtitle')}</div>
        </div>
      </div>
      <div className="topActions">
        <a className="navLink" href="/">{t('nav.overview')}</a>
        <a className="navLink" href="/status">{t('nav.status')}</a>
        <a className="navLink" href="/support">{t('nav.support')}</a>
        <a className="navLink" href="/agreements">{t('nav.agreements')}</a>
        <a className="navLink" href="/policies">{t('nav.policies')}</a>
        <a className="navLink" href="/settings">{t('nav.settings')}</a>
        <div className="statusPill">● {t('topbar.liveOps')}</div>
        <LocaleSwitcher />
        <ThemeToggle />
      </div>
    </div>
  );
}
