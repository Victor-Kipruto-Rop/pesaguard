import { NextResponse } from 'next/server';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export async function POST(req: Request) {
  try {
    // attempt to notify backend (best-effort)
    try {
      const backendUrl = (BASE ? BASE.replace(/\/$/, '') : '') + '/api/auth/logout';
      await fetch(backendUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', cache: 'no-store' });
    } catch (e) {
      // ignore
    }

    const response = NextResponse.json({ ok: true });
    // clear cookies
    const cookieDomain = process.env.AUTH_COOKIE_DOMAIN ? `; Domain=${process.env.AUTH_COOKIE_DOMAIN}` : '';
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    response.headers.append('Set-Cookie', `auth_access=; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=0`);
    response.headers.append('Set-Cookie', `auth_refresh=; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=0`);
    return response;
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'unexpected' }, { status: 500 });
  }
}
