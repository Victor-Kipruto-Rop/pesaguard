'use client';

import { usePathname } from 'next/navigation';
import { useLocale } from '../lib/i18n';
import PulseLine from './PulseLine';

export default function PublicNav() {
  const pathname = usePathname();
  const { t } = useLocale();

  const links = [
    { href: '/landing', label: t('publicNav.product') },
    { href: '/pricing', label: t('publicNav.pricing') },
    { href: '/about', label: t('publicNav.about') },
    { href: '/security', label: t('publicNav.security') },
    { href: '/docs', label: t('publicNav.docs') },
    { href: '/contact', label: t('publicNav.contact') },
  ];

  return (
    <header className="publicNav">
      <div className="publicNavInner">
        <a href="/landing" className="publicBrand">
          <span className="brandMark">PG</span>
          <span>
            <strong>{t('brand.name')}</strong>
            <PulseLine className="brandPulse" height={16} />
          </span>
        </a>
        <nav className="publicLinks">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={pathname === link.href ? 'active' : ''}
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="publicActions">
          <a className="secondaryBtn" href="/auth/login">{t('publicNav.signIn')}</a>
          <a className="primaryBtn" href="/contact">{t('publicNav.requestDemo')}</a>
        </div>
      </div>
    </header>
  );
}
