import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001';

async function forward(req: Request, method: string) {
  const url = new URL(req.url);
  const suffix = url.searchParams.get('path') || '';
  const target = `${API_BASE.replace(/\/$/, '')}/account/me${suffix}`;
  const cookieHeader = req.headers.get('cookie') || '';
  const token = cookieHeader.match(/(?:^|;\s*)auth_access=([^;]+)/)?.[1];
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (token) headers.Authorization = `Bearer ${decodeURIComponent(token)}`;
  const body = method === 'GET' || method === 'DELETE' ? undefined : await req.text();
  if (body) headers['Content-Type'] = 'application/json';

  try {
    const response = await fetch(target, { method, headers, body, cache: 'no-store' });
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { 'Content-Type': response.headers.get('content-type') || 'application/json' },
    });
  } catch {
    return NextResponse.json({ error: 'account_service_unavailable' }, { status: 503 });
  }
}

export async function GET(req: Request) { return forward(req, 'GET'); }
export async function PATCH(req: Request) { return forward(req, 'PATCH'); }
export async function POST(req: Request) { return forward(req, 'POST'); }
export async function DELETE(req: Request) { return forward(req, 'DELETE'); }
