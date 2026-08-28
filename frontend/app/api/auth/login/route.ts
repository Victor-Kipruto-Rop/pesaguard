import { NextResponse } from 'next/server';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const backendUrl = (BASE ? BASE.replace(/\/$/, '') : '') + '/api/auth/login';
    const res = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });

    // extract common token shapes
    const accessToken = data.accessToken ?? data.access_token ?? data.token;
    const refreshToken = data.refreshToken ?? data.refresh_token;
    const expiresIn = data.expiresIn ?? data.expires_in ?? data.expires ?? 3600;

    const cookies: string[] = [];
    const cookieDomain = process.env.AUTH_COOKIE_DOMAIN ? `; Domain=${process.env.AUTH_COOKIE_DOMAIN}` : '';
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    if (accessToken) {
      const maxAge = Number(expiresIn) || 3600;
      cookies.push(`auth_access=${encodeURIComponent(accessToken)}; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=${maxAge}`);
    }
    if (refreshToken) {
      // refresh expiry configurable via AUTH_REFRESH_MAX_AGE (seconds), fallback 30 days
      const refreshMaxAge = Number(process.env.AUTH_REFRESH_MAX_AGE) || 60 * 60 * 24 * 30;
      cookies.push(`auth_refresh=${encodeURIComponent(refreshToken)}; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=${refreshMaxAge}`);
    }

    const response = NextResponse.json({ ok: true, accessToken, refreshToken, expiresIn });
    for (const c of cookies) response.headers.append('Set-Cookie', c);
    return response;
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'unexpected' }, { status: 500 });
  }
}
