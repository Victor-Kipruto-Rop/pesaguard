'use client';

import { useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useLocale } from '../../lib/i18n';

export default function AccountPage() {
  const { t } = useLocale();
  const [darajaKey] = useState('••••••••••••4F2A');
  const [team, setTeam] = useState([
    { name: 'Finance Ops', email: 'ops@tenant.example', role: 'Operator' },
    { name: 'Audit Lead', email: 'audit@tenant.example', role: 'Viewer' },
  ]);
  const [inviteEmail, setInviteEmail] = useState('');

  const invite = () => {
    if (!inviteEmail.trim()) return;
    setTeam([...team, { name: inviteEmail.split('@')[0], email: inviteEmail, role: 'Operator' }]);
    setInviteEmail('');
  };

  return (
    <main className="shell">
      <PageHeader eyebrow={t('account.eyebrow')} title={t('account.title')} summary={t('account.summary')} />

      <section className="grid twoUp">
        <article className="card">
          <div className="sectionTitle">{t('account.integrationsTitle')}</div>
          <div className="row"><span>{t('account.darajaConsumerKey')}</span><strong className="mono">{darajaKey}</strong></div>
          <div className="row"><span>{t('account.darajaConsumerSecret')}</span><strong className="mono">{darajaKey}</strong></div>
          <div className="row"><span>{t('account.callbackUrl')}</span><strong className="mono">/webhook/mpesa/confirmation</strong></div>
          <p className="muted small">{t('account.maskedHint')}</p>
        </article>
        <article className="card">
          <div className="sectionTitle">{t('account.connectedAccounts')}</div>
          <ul className="stackList">
            <li>M-Pesa Paybill · Active</li>
            <li>Daraja Sandbox · Test mode</li>
          </ul>
        </article>
      </section>

      <section className="card">
        <div className="sectionTitle">{t('account.teamTitle')}</div>
        <div className="tableWrap">
          <table>
            <thead><tr><th>{t('contact.name')}</th><th>{t('contact.email')}</th><th>{t('account.role')}</th></tr></thead>
            <tbody>
              {team.map((member) => (
                <tr key={member.email}><td>{member.name}</td><td>{member.email}</td><td>{member.role}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="toolbar" style={{ marginTop: 16 }}>
          <input value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder={t('account.invitePlaceholder')} />
          <button onClick={invite}>{t('account.invite')}</button>
        </div>
      </section>
    </main>
  );
}
