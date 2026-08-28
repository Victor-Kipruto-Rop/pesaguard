import { NextResponse } from 'next/server';

// Simple endpoint to confirm a valid session via cookies. Backend may provide
// a user payload; here we only check whether the backend accepts cookies.

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';

export async function GET(req: Request) {
  try {
    const backendUrl = (BASE ? BASE.replace(/\/$/, '') : '') + '/api/auth/me';
    // forward cookie from incoming request to backend
    const res = await fetch(backendUrl, { method: 'GET', headers: { Cookie: req.headers.get('cookie') ?? '' }, cache: 'no-store' });
    if (!res.ok) return NextResponse.json({ ok: false }, { status: 401 });
    const data = await res.json();
    return NextResponse.json({ ok: true, user: data });
  } catch (err: any) {
    return NextResponse.json({ ok: false }, { status: 500 });
  }
}
