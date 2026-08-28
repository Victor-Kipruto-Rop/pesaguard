import type { ReactNode } from 'react';

export const metadata = {
  title: 'PesaGuard Tenant Admin',
  description: 'Tenant admin workspace for SACCOs and tenant-level operations',
};

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
