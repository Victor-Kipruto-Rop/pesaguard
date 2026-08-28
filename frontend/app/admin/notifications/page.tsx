"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminNotificationsPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Notifications"
        summary="Configure and review alert notifications, email, SMS, and push delivery."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/notifications/notification-settings" className="secondaryBtn">Notification settings</Link>
          <Link href="/admin/notifications/alerts" className="secondaryBtn">Alerts</Link>
          <Link href="/admin/notifications/email" className="secondaryBtn">Email</Link>
          <Link href="/admin/notifications/sms" className="secondaryBtn">SMS</Link>
          <Link href="/admin/notifications/push" className="secondaryBtn">Push</Link>
          <Link href="/admin/notifications/notification-history" className="secondaryBtn">Notification history</Link>
        </div>
      </section>
    </main>
  );
}
