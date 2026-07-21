import './globals.css';
import AuthGate from '../components/AuthGate';
import AppShell from '../components/AppShell';

export const metadata = {
  title: 'PesaGuard',
  description: 'Premium reconciliation operations for M-Pesa ecosystems',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
      </head>
      <body>
        <AppShell>
          <AuthGate>{children}</AuthGate>
        </AppShell>
      </body>
    </html>
  );
}
