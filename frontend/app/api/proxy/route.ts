import { NextResponse } from 'next/server';

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const path = body.path ?? '';
    const method = body.method ?? 'GET';
    const headers = body.headers ?? {};
    const payload = body.body ?? null;

    const target = (BASE ? BASE.replace(/\/$/, '') : '') + (path.startsWith('/') ? path : '/' + path);

    const forwardHeaders: Record<string, string> = { 'Content-Type': 'application/json', ...headers };
    // forward incoming cookie to backend so backend can validate session via cookies
    const incomingCookies = req.headers.get('cookie');
    if (incomingCookies) forwardHeaders['Cookie'] = incomingCookies;

    const res = await fetch(target, { method, headers: forwardHeaders, body: payload ? JSON.stringify(payload) : undefined, cache: 'no-store' });
    const responseBody = await res.text();

    const out = new NextResponse(responseBody, { status: res.status });
    // forward set-cookie headers
    const setCookies = res.headers.get('set-cookie');
    if (setCookies) out.headers.append('Set-Cookie', setCookies);
    // copy content-type
    const ct = res.headers.get('content-type');
    if (ct) out.headers.set('Content-Type', ct);
    return out;
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'unexpected' }, { status: 500 });
  }
}
