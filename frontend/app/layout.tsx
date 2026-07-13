import './globals.css';
import AuthGate from '../components/AuthGate';
import ThemeToggle from '../components/ThemeToggle';
import Sidebar from '../components/Sidebar';
import LocaleSwitcher from '../components/LocaleSwitcher';

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
            <div className="topbar">
              <div className="brandBlock">
                <div className="brandMark">PG</div>
                <div>
                  <div className="brand">PesaGuard</div>
                  <div className="brandSub">Premium reconciliation command center</div>
                </div>
              </div>
              <div className="topActions">
                <a className="navLink" href="/">Overview</a>
                <a className="navLink" href="/status">Status</a>
                <a className="navLink" href="/support">Support</a>
                <a className="navLink" href="/agreements">Agreements</a>
                <a className="navLink" href="/policies">Policies</a>
                <a className="navLink" href="/settings">Settings</a>
                <div className="statusPill">● Live ops</div>
                <LocaleSwitcher />
                <ThemeToggle />
              </div>
            </div>
            <AuthGate>{children}</AuthGate>
          </div>
        </div>
      </body>
    </html>
  );
}
