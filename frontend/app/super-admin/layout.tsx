import type { ReactNode } from 'react';
import AdminGate from '../../components/AdminGate';

export const metadata = {
  title: 'PesaGuard Super Admin',
  description: 'Premium super-admin console for PesaGuard tenant operations',
};

export default function SuperAdminLayout({ children }: { children: ReactNode }) {
  return <AdminGate>{children}</AdminGate>;
}
