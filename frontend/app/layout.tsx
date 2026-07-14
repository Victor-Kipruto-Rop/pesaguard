import './globals.css';
import AuthGate from '../components/AuthGate';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';

export const metadata = {
  title: 'PesaGuard',
  description: 'Premium reconciliation operations for M-Pesa ecosystems',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="themeShell">
          <Sidebar />
          <div className="mainContent">
            <TopBar />
            <AuthGate>{children}</AuthGate>
          </div>
        </div>
      </body>
    </html>
  );
}
