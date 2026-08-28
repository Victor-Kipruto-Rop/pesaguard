"use client";

import Link from 'next/link';
import PageHeader from '../../components/PageHeader';

export default function NotificationsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Notifications"
        title="Notifications hub"
        summary="Review inbox items, reminders, announcements, and settings."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/notifications/inbox" className="secondaryBtn">Inbox</Link>
          <Link href="/notifications/alerts" className="secondaryBtn">Alerts</Link>
          <Link href="/notifications/announcements" className="secondaryBtn">Announcements</Link>
          <Link href="/notifications/reminders" className="secondaryBtn">Reminders</Link>
          <Link href="/notifications/notification-settings" className="secondaryBtn">Settings</Link>
          <Link href="/notifications/archived" className="secondaryBtn">Archived</Link>
        </div>
      </section>
    </main>
  );
}
