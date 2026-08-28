import { NextResponse } from 'next/server';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export async function POST(req: Request) {
  try {
    // server-side refresh using cookie `auth_refresh` (backend contract may vary)
    // If the backend expects the refresh token in body, forward it from cookie.

    // Read cookies from incoming request
    const cookieHeader = req.headers.get('cookie') ?? '';
    const match = cookieHeader.match(/(?:^|; )auth_refresh=([^;]+)/);
    const refreshToken = match ? decodeURIComponent(match[1]) : undefined;

    const backendUrl = (BASE ? BASE.replace(/\/$/, '') : '') + '/api/auth/refresh';
    const backendRes = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(refreshToken ? { refreshToken } : {}),
      cache: 'no-store',
    });

    const data = await backendRes.json();
    if (!backendRes.ok) return NextResponse.json(data, { status: backendRes.status });

    const accessToken = data.accessToken ?? data.access_token ?? data.token;
    const refresh = data.refreshToken ?? data.refresh_token;
    const expiresIn = data.expiresIn ?? data.expires_in ?? data.expires ?? 3600;

    const response = NextResponse.json({ ok: true, accessToken, refreshToken: refresh, expiresIn });
    const cookieDomain = process.env.AUTH_COOKIE_DOMAIN ? `; Domain=${process.env.AUTH_COOKIE_DOMAIN}` : '';
    const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
    if (accessToken) {
      response.headers.append('Set-Cookie', `auth_access=${encodeURIComponent(accessToken)}; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=${Number(expiresIn)}`);
    }
    if (refresh) {
      const refreshMaxAge = Number(process.env.AUTH_REFRESH_MAX_AGE) || 60 * 60 * 24 * 30;
      response.headers.append('Set-Cookie', `auth_refresh=${encodeURIComponent(refresh)}; Path=/; HttpOnly; SameSite=Strict${secure}${cookieDomain}; Max-Age=${refreshMaxAge}`);
    }
    return response;
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'unexpected' }, { status: 500 });
  }
}
