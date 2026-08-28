"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function PublicPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Public"
        title="Public site"
        summary="Browse product information, pricing, documentation, and customer resources."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/public/home" className="secondaryBtn">Home</Link>
          <Link href="/public/features" className="secondaryBtn">Features</Link>
          <Link href="/public/pricing" className="secondaryBtn">Pricing</Link>
          <Link href="/public/customers" className="secondaryBtn">Customers</Link>
          <Link href="/public/contact" className="secondaryBtn">Contact</Link>
          <Link href="/public/documentation" className="secondaryBtn">Documentation</Link>
        </div>
      </section>
    </main>
  );
}
