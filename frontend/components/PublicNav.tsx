'use client';

import { usePathname } from 'next/navigation';
import { useLocale } from '../lib/i18n';
import PulseLine from './PulseLine';
import { Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function PublicNav() {
  const pathname = usePathname();
  const { t } = useLocale();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const links = [
    { href: '/public/features', label: t('publicNav.product') },
    { href: '/public/pricing', label: t('publicNav.pricing') },
    { href: '/public/about', label: t('publicNav.about') },
    { href: '/public/security', label: t('publicNav.security') },
    { href: '/public/documentation', label: t('publicNav.docs') },
    { href: '/public/contact', label: t('publicNav.contact') },
  ];

  return (
    <header className="publicNav">
      <div className="publicNavInner">
        <a href="/public/home" className="publicBrand">
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
          <a className="primaryBtn" href="/public/book-demo">{t('publicNav.requestDemo')}</a>
        </div>
        <button 
          className="mobileMenuToggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
      {mobileMenuOpen && (
        <div className="mobileMenu">
          <nav className="mobileLinks">
            {links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className={pathname === link.href ? 'active' : ''}
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mobileActions">
            <a className="mobileSecondaryBtn" href="/auth/login">{t('publicNav.signIn')}</a>
            <a className="mobilePrimaryBtn" href="/public/book-demo">{t('publicNav.requestDemo')}</a>
          </div>
        </div>
      )}
    </header>
  );
}
