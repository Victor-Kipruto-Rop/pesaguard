'use client';

import ThemeToggle from './ThemeToggle';
import LocaleSwitcher from './LocaleSwitcher';
import { useLocale } from '../lib/i18n';
import { useRouter } from 'next/navigation';
import { clearTokens } from '../lib/fetchAuth';
import apiProxy from '../lib/apiProxy';

export default function TopBar() {
  const { t } = useLocale();
  const router = useRouter();

  async function handleLogout() {
    try {
      // server-side logout clears cookies
      await apiProxy('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      // ignore
    }
    clearTokens();
    router.replace('/auth/login');
  }

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
        <button className="btn btn-ghost" onClick={handleLogout} aria-label="Logout">
          {t('nav.logout') ?? 'Logout'}
        </button>
      </div>
    </div>
  );
}
