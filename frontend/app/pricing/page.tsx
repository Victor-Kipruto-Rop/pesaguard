'use client';

import { useLocale } from '../../lib/i18n';
import PageHeader from '../../components/PageHeader';

export default function PricingPage() {
  const { t } = useLocale();
  const tiers = t<{ name: string; price: string; summary: string; features: string[] }[]>('pricing.tiers');
  const faq = t<{ q: string; a: string }[]>('pricing.faq');

  return (
    <main className="publicMain">
      <PageHeader eyebrow={t('pricing.eyebrow')} title={t('pricing.title')} summary={t('pricing.summary')} />

      <section className="readinessGrid">
        {tiers.map((tier) => (
          <article key={tier.name} className="assetCard">
            <div className="eyebrow">{tier.name}</div>
            <h3 className="mono">{tier.price}</h3>
            <p className="muted">{tier.summary}</p>
            <ul className="stackList">
              {tier.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <a className="primaryBtn" href="/contact">{t('pricing.cta')}</a>
          </article>
        ))}
      </section>

      <section className="card">
        <div className="sectionTitle">{t('pricing.faqTitle')}</div>
        {faq.map((item) => (
          <div key={item.q} className="row" style={{ flexDirection: 'column', alignItems: 'flex-start' }}>
            <strong>{item.q}</strong>
            <span className="muted">{item.a}</span>
          </div>
        ))}
      </section>
    </main>
  );
}
