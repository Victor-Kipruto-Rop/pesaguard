'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  Bell, Check, ChevronRight, CircleUserRound, Copy, Eye, KeyRound, Laptop,
  LoaderCircle, LockKeyhole, Mail, Monitor, Palette, Phone, ShieldCheck,
  Trash2, UserRound, WandSparkles,
} from 'lucide-react';
import AccountPageShell from './AccountPageShell';

type View = 'profile' | 'edit-profile' | 'change-email' | 'change-phone' | 'change-password' | 'avatar' | 'appearance' | 'preferences' | 'language' | 'timezone' | 'privacy' | 'security' | 'active-sessions' | 'connected-devices' | 'api-tokens' | 'delete-account';
type Account = {
  user_id: string; username: string; display_name: string; email: string; job_title: string; phone: string;
  avatar_url: string; timezone: string; language: string; appearance: string;
  privacy: Record<string, boolean>; notifications: Record<string, boolean>;
  api_tokens: Array<{ id: string; label: string; prefix: string; scopes: string[]; created_at: string; last_used_at?: string | null }>;
};

const meta: Record<View, { title: string; subtitle: string; section: string }> = {
  profile: { title: 'Your profile', subtitle: 'Your identity, preferences, and security posture in one composed workspace.', section: 'Profile' },
  'edit-profile': { title: 'Edit profile', subtitle: 'Keep the details colleagues see in operations and audit workflows accurate.', section: 'Identity' },
  'change-email': { title: 'Change email', subtitle: 'Request a verified update to the email used for sign-in and recovery.', section: 'Identity' },
  'change-phone': { title: 'Phone number', subtitle: 'Keep your recovery and security notification number current.', section: 'Identity' },
  'change-password': { title: 'Change password', subtitle: 'Start a verified password change flow for your account.', section: 'Privacy & security' },
  avatar: { title: 'Profile image', subtitle: 'Use a recognisable image to make operational hand-offs more human.', section: 'Identity' },
  appearance: { title: 'Appearance', subtitle: 'Tune the visual environment around the way you prefer to work.', section: 'Preferences' },
  preferences: { title: 'Notifications', subtitle: 'Decide which messages deserve your attention and when.', section: 'Preferences' },
  language: { title: 'Language', subtitle: 'Choose the language your workspace uses for labels and alerts.', section: 'Preferences' },
  timezone: { title: 'Timezone', subtitle: 'Keep events, reports, and audit history aligned with your working day.', section: 'Preferences' },
  privacy: { title: 'Privacy', subtitle: 'Control how sensitive account information appears throughout PesaGuard.', section: 'Privacy & security' },
  security: { title: 'Security centre', subtitle: 'Review the controls protecting access to your operational workspace.', section: 'Privacy & security' },
  'active-sessions': { title: 'Active sessions', subtitle: 'See where your account is currently active and end access when needed.', section: 'Privacy & security' },
  'connected-devices': { title: 'Connected devices', subtitle: 'Review devices with access to your account.', section: 'Privacy & security' },
  'api-tokens': { title: 'API tokens', subtitle: 'Create and revoke tightly scoped credentials for your automations.', section: 'Developer' },
  'delete-account': { title: 'Delete account', subtitle: 'Start a protected account deletion request after reviewing the impact.', section: 'Danger zone' },
};

const nav = [
  ['profile', 'Profile', CircleUserRound], ['edit-profile', 'Personal details', UserRound], ['appearance', 'Appearance', Palette], ['preferences', 'Notifications', Bell], ['language', 'Language', WandSparkles], ['timezone', 'Timezone', Monitor], ['privacy', 'Privacy', Eye], ['security', 'Security', ShieldCheck], ['active-sessions', 'Sessions', Laptop], ['api-tokens', 'API tokens', KeyRound],
] as const;

async function accountRequest(path = '', method = 'GET', body?: unknown) {
  const response = await fetch(`/api/account?path=${encodeURIComponent(path)}`, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined, cache: 'no-store' });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || data.error || 'Unable to save your changes.');
  return data;
}

export default function AccountExperience({ view }: { view: View }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [status, setStatus] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [tokenName, setTokenName] = useState('');
  const [newSecret, setNewSecret] = useState('');
  const info = meta[view];

  const initials = useMemo(() => (account?.display_name || account?.username || 'P').split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase(), [account]);
  const reload = async () => {
    try { const data = await accountRequest(); setAccount(data.account); }
    catch (error) { setStatus(error instanceof Error ? error.message : 'Unable to load account settings.'); }
  };
  useEffect(() => { void reload(); }, []);

  async function save(values: Record<string, unknown>) {
    setSaving(true); setStatus('');
    try { const data = await accountRequest('', 'PATCH', values); setAccount(data.account); setStatus('Changes saved.'); }
    catch (error) { setStatus(error instanceof Error ? error.message : 'Unable to save your changes.'); }
    finally { setSaving(false); }
  }
  async function handleForm(event: FormEvent<HTMLFormElement>, keys: string[]) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const values = Object.fromEntries(keys.map((key) => [key, String(form.get(key) || '')])); await save(values);
  }
  async function credentialRequest(type: string, email?: string) {
    setSaving(true); setStatus('');
    try { const data = await accountRequest('/credential-requests', 'POST', { type, email }); setStatus(data.message); }
    catch (error) { setStatus(error instanceof Error ? error.message : 'Unable to submit your request.'); }
    finally { setSaving(false); }
  }
  async function createToken(event: FormEvent) {
    event.preventDefault(); if (!tokenName.trim()) return; setSaving(true); setStatus('');
    try { const data = await accountRequest('/api-tokens', 'POST', { label: tokenName, scopes: ['read:discrepancies'] }); setNewSecret(data.secret); setTokenName(''); await reload(); setStatus('Token created. Copy it now — it will not be shown again.'); }
    catch (error) { setStatus(error instanceof Error ? error.message : 'Unable to create token.'); } finally { setSaving(false); }
  }
  async function revokeToken(id: string) { setSaving(true); try { const data = await accountRequest(`/api-tokens/${id}`, 'DELETE'); setAccount(data.account); setStatus('Token revoked.'); } catch (error) { setStatus(error instanceof Error ? error.message : 'Unable to revoke token.'); } finally { setSaving(false); } }

  const profileForm = <form className="accountStudioForm" onSubmit={(event) => handleForm(event, ['display_name', 'job_title', 'phone'])}><Field label="Full name" name="display_name" value={account?.display_name}/><Field label="Role or job title" name="job_title" value={account?.job_title} placeholder="e.g. Operations manager"/><Field label="Phone number" name="phone" value={account?.phone} placeholder="+254 700 000 000"/><SaveButton saving={saving} label="Save profile"/></form>;
  const emailForm = <form className="accountStudioForm" onSubmit={(event) => { event.preventDefault(); const email = String(new FormData(event.currentTarget).get('email') || ''); void credentialRequest('email_change', email); }}><Field label="Current sign-in email" name="current" value={account?.email || account?.username} disabled/><Field label="New work email" name="email" placeholder="you@company.com" type="email"/><button className="accountSave" disabled={saving}><Mail size={16}/>Request verification</button><p className="accountFinePrint">For your protection, a verified identity flow completes sign-in email changes.</p></form>;

  let content: React.ReactNode = profileForm;
  if (view === 'profile') content = <div className="accountOverview"><div className="accountIdentityCard"><div className="accountAvatar">{account?.avatar_url ? <img src={account.avatar_url} alt=""/> : initials}</div><div><p className="accountKicker">SIGNED IN AS</p><h2>{account?.display_name || account?.username || 'Loading…'}</h2><p>{account?.job_title || 'PesaGuard member'} · {account?.email || account?.username}</p></div><a href="/account/edit-profile" className="accountTextAction">Edit details <ChevronRight size={15}/></a></div><div className="accountQuickGrid"><Quick label="Language" value={account?.language === 'sw' ? 'Swahili' : 'English'} href="/account/language"/><Quick label="Timezone" value={account?.timezone || 'Africa/Nairobi'} href="/account/timezone"/><Quick label="Security" value="Protected" href="/account/security"/></div><section className="accountFeatureCard"><div><span className="accountFeatureIcon"><ShieldCheck size={21}/></span><h3>Your account is ready for the work ahead.</h3><p>Keep your identity and preferences fresh so the right information reaches you at the right time.</p></div><a href="/account/security" className="accountTextAction">Review security <ChevronRight size={15}/></a></section></div>;
  if (view === 'edit-profile' || view === 'change-phone') content = profileForm;
  if (view === 'change-email') content = emailForm;
  if (view === 'avatar') content = <form className="accountStudioForm" onSubmit={(event) => handleForm(event, ['avatar_url'])}><div className="avatarEditor"><div className="accountAvatar large">{account?.avatar_url ? <img src={account.avatar_url} alt=""/> : initials}</div><div><h3>A recognisable profile</h3><p>Paste a secure image URL. Square images work best.</p></div></div><Field label="Image URL" name="avatar_url" value={account?.avatar_url} placeholder="https://…"/><SaveButton saving={saving} label="Update profile image"/></form>;
  if (view === 'appearance') content = <div className="accountChoiceGrid">{[['dark', 'Dark', 'Low-glare contrast for focused operations.'], ['light', 'Light', 'A crisp, spacious surface for daytime review.'], ['system', 'System', 'Follow your device preference automatically.']].map(([value, title, description]) => <button className={`accountChoice ${account?.appearance === value ? 'selected' : ''}`} onClick={() => void save({ appearance: value })} key={value}><span className="choiceRadio"/><b>{title}</b><small>{description}</small></button>)}</div>;
  if (view === 'language') content = <div className="accountChoiceGrid">{[['en', 'English', 'Default language for global payment operations.'], ['sw', 'Swahili', 'A localised experience for East African teams.']].map(([value, title, description]) => <button className={`accountChoice ${account?.language === value ? 'selected' : ''}`} onClick={() => void save({ language: value })} key={value}><span className="choiceRadio"/><b>{title}</b><small>{description}</small></button>)}</div>;
  if (view === 'timezone') content = <form className="accountStudioForm" onSubmit={(event) => handleForm(event, ['timezone'])}><label className="accountField"><span>Timezone</span><select name="timezone" defaultValue={account?.timezone || 'Africa/Nairobi'}><option value="Africa/Nairobi">East Africa Time — Nairobi</option><option value="UTC">Coordinated Universal Time</option><option value="Africa/Lagos">West Africa Time — Lagos</option><option value="Europe/London">London</option></select></label><SaveButton saving={saving} label="Save timezone"/></form>;
  if (view === 'preferences' || view === 'privacy') { const group = view === 'preferences' ? 'notifications' : 'privacy'; const labels = view === 'preferences' ? [['email_alerts', 'Operational email alerts', 'Important exception and security messages.'], ['weekly_digest', 'Weekly operating digest', 'A considered summary of the week’s activity.'], ['product_updates', 'Product updates', 'Occasional notes about new PesaGuard capabilities.']] : [['mask_sensitive_data', 'Mask sensitive data', 'Show only what is needed in daily workflows.'], ['share_profile', 'Profile visibility', 'Allow limited profile details to be visible to colleagues.'], ['security_alerts', 'Security alerts', 'Always notify me about material account changes.']]; const values = (account?.[group] || {}) as Record<string, boolean>; content = <div className="accountToggleList">{labels.map(([key, title, desc]) => <button className="accountToggle" onClick={() => void save({ [group]: { ...values, [key]: !values[key] } })} key={key}><span><b>{title}</b><small>{desc}</small></span><i className={values[key] ? 'on' : ''}/></button>)}</div>; }
  if (view === 'security') content = <div className="accountSecurityList"><SecurityRow icon={<LockKeyhole size={19}/>} title="Sign-in credentials" text="Changes are verified by your identity provider before they take effect." href="/account/change-password" action="Request change"/><SecurityRow icon={<Laptop size={19}/>} title="Active sessions" text="Review the browser sessions currently associated with your account." href="/account/active-sessions" action="Review sessions"/><SecurityRow icon={<KeyRound size={19}/>} title="Automation credentials" text={`${account?.api_tokens.length || 0} active API token${account?.api_tokens.length === 1 ? '' : 's'} in your account.`} href="/account/api-tokens" action="Manage tokens"/></div>;
  if (view === 'active-sessions' || view === 'connected-devices') content = <div className="accountSession"><div className="sessionDevice"><span className="sessionDeviceIcon"><Laptop size={21}/></span><div><b>This browser</b><small>Current authenticated PesaGuard session · Active now</small></div><span className="accountLive"><i/>Current</span></div><p className="accountFinePrint">PesaGuard records device and session activity through your authenticated identity provider. Ending this session signs you out of this browser.</p><button className="accountOutline" onClick={() => { void fetch('/api/auth/logout', { method: 'POST' }); window.location.href = '/auth/login'; }}>Sign out of this browser</button></div>;
  if (view === 'api-tokens') content = <div className="accountTokens"><form className="tokenCreate" onSubmit={createToken}><div><label htmlFor="token-name">New token name</label><input id="token-name" value={tokenName} onChange={(event) => setTokenName(event.target.value)} placeholder="e.g. reconciliation-export"/></div><button className="accountSave" disabled={saving || !tokenName.trim()}><KeyRound size={16}/>Create token</button></form>{newSecret && <div className="tokenSecret"><div><b>Copy your new token now</b><code>{newSecret}</code></div><button aria-label="Copy token" onClick={() => void navigator.clipboard.writeText(newSecret)}><Copy size={17}/></button></div>}<div className="tokenList">{account?.api_tokens.length ? account.api_tokens.map((token) => <div className="tokenRow" key={token.id}><span className="tokenMark"><KeyRound size={17}/></span><div><b>{token.label}</b><small>{token.prefix}•••• · {token.scopes.join(', ')}</small></div><button onClick={() => void revokeToken(token.id)} className="accountDangerLink">Revoke</button></div>) : <div className="accountEmpty">No API tokens yet. Create one only for an automation you trust.</div>}</div></div>;
  if (view === 'delete-account') content = <div className="accountDeletion"><span className="deletionIcon"><Trash2 size={23}/></span><h3>Start an account deletion request</h3><p>This removes your PesaGuard account after a protected verification and review process. It does not erase organisation-level payment records.</p><button className="accountDangerButton" disabled={saving} onClick={() => void credentialRequest('account_deletion')}><Trash2 size={16}/>Request account deletion</button></div>;
  if (view === 'change-password') content = <div className="accountDeletion"><span className="deletionIcon neutral"><LockKeyhole size={23}/></span><h3>Request a credential update</h3><p>Sign-in credentials are protected by your identity provider. We’ll begin a verified password-change flow for your account.</p><button className="accountSave" disabled={saving} onClick={() => void credentialRequest('password_change')}><LockKeyhole size={16}/>Request password change</button></div>;

  return <AccountPageShell title={info.title} subtitle={info.subtitle}><div className="accountStudio"><aside className="accountStudioNav"><p>{info.section}</p>{nav.map(([key, label, Icon]) => <a key={key} href={`/account/${key}`} className={view === key ? 'active' : ''}><Icon size={16}/>{label}</a>)}<a href="/account/delete-account" className={view === 'delete-account' ? 'danger active' : 'danger'}><Trash2 size={16}/>Delete account</a></aside><section className="accountStudioPanel">{status && <div className={`accountNotice ${status === 'Changes saved.' || status.includes('created') || status.includes('revoked') ? 'success' : ''}`}>{status.includes('saved') || status.includes('created') || status.includes('revoked') ? <Check size={16}/> : <ShieldCheck size={16}/>} {status}</div>}{account === null && !status ? <div className="accountLoading"><LoaderCircle size={20}/>Loading your account…</div> : content}</section></div></AccountPageShell>;
}

function Field({ label, name, value, placeholder, type = 'text', disabled = false }: { label: string; name: string; value?: string; placeholder?: string; type?: string; disabled?: boolean }) { return <label className="accountField"><span>{label}</span><input name={name} type={type} defaultValue={value || ''} placeholder={placeholder} disabled={disabled}/></label>; }
function SaveButton({ saving, label }: { saving: boolean; label: string }) { return <button className="accountSave" disabled={saving}>{saving ? <LoaderCircle className="spin" size={16}/> : <Check size={16}/>} {saving ? 'Saving…' : label}</button>; }
function Quick({ label, value, href }: { label: string; value: string; href: string }) { return <a href={href}><span>{label}</span><b>{value}</b><ChevronRight size={15}/></a>; }
function SecurityRow({ icon, title, text, href, action }: { icon: React.ReactNode; title: string; text: string; href: string; action: string }) { return <a href={href}><span className="securityIcon">{icon}</span><div><b>{title}</b><small>{text}</small></div><span>{action}<ChevronRight size={15}/></span></a>; }
