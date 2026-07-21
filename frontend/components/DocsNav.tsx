'use client';

import { usePathname } from 'next/navigation';
import { useLocale } from '../lib/i18n';

const LINKS = [
  { href: '/docs', labelKey: 'docs.home' },
  { href: '/docs/getting-started', labelKey: 'docs.gettingStarted' },
  { href: '/docs/api', labelKey: 'docs.api' },
  { href: '/docs/webhooks', labelKey: 'docs.webhooks' },
  { href: '/docs/faq', labelKey: 'docs.faq' },
  { href: '/docs/changelog', labelKey: 'docs.changelog' },
  { href: '/docs/glossary', labelKey: 'docs.glossary' },
];

export default function DocsNav() {
  const pathname = usePathname();
  const { t } = useLocale();

  return (
    <nav className="docsNav" aria-label="Documentation">
      {LINKS.map((link) => (
        <a key={link.href} href={link.href} className={pathname === link.href ? 'active' : ''}>
          {t(link.labelKey)}
        </a>
      ))}
    </nav>
  );
}
