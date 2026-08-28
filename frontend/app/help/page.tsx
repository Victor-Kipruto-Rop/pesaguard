"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function HelpPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Help"
        title="Help center"
        summary="Find guides, support channels, and troubleshooting resources."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/help/help-center" className="secondaryBtn">Help center</Link>
          <Link href="/help/getting-started" className="secondaryBtn">Getting started</Link>
          <Link href="/help/documentation" className="secondaryBtn">Documentation</Link>
          <Link href="/help/troubleshooting" className="secondaryBtn">Troubleshooting</Link>
          <Link href="/help/create-ticket" className="secondaryBtn">Create ticket</Link>
          <Link href="/help/ticket-history" className="secondaryBtn">Ticket history</Link>
        </div>
      </section>
    </main>
  );
}
