"use client";

import Link from 'next/link';
import PageHeader from '../../../components/PageHeader';

export default function AdminUsersPage() {
  return (
    <main className="shell">
      <PageHeader
        eyebrow="Admin"
        title="Users & access"
        summary="Manage user accounts, roles, permissions, and login activity."
      />

      <section className="card">
        <div style={{ display: 'grid', gap: 12 }}>
          <Link href="/admin/users/users" className="secondaryBtn">Users</Link>
          <Link href="/admin/users/create-user" className="secondaryBtn">Create user</Link>
          <Link href="/admin/users/roles" className="secondaryBtn">Roles</Link>
          <Link href="/admin/users/permissions" className="secondaryBtn">Permissions</Link>
          <Link href="/admin/users/teams" className="secondaryBtn">Teams</Link>
          <Link href="/admin/users/login-history" className="secondaryBtn">Login history</Link>
          <Link href="/admin/users/activity-log" className="secondaryBtn">Activity log</Link>
        </div>
      </section>
    </main>
  );
}
