'use client';

import SuperAdminSectionPage from '../../../components/SuperAdminSectionPage';

const links = [
  { title: 'Users', href: '/super-admin/users/users', summary: 'Manage operator and admin user records.' },
  { title: 'Teams', href: '/super-admin/users/teams', summary: 'Organize users into operational teams.' },
  { title: 'Roles', href: '/super-admin/users/roles', summary: 'Define role-based access levels.' },
  { title: 'Permissions', href: '/super-admin/users/permissions', summary: 'Review and adjust permission assignments.' },
  { title: 'Invitations', href: '/super-admin/users/invitations', summary: 'Pending onboarding and invite management.' },
  { title: 'Login history', href: '/super-admin/users/login-history', summary: 'Authentication and access history.' },
];

export default function AdminUsersPage() {
  return (
    <SuperAdminSectionPage
      eyebrow="Super admin"
      title="Users & Roles"
      summary="Govern access, permissions and team-based administration."
      links={links}
    />
  );
}
