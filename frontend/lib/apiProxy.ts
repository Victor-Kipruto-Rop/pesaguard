export async function apiProxy(path: string, opts?: { method?: string; headers?: Record<string,string>; body?: any }) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
  const body = { path, method: opts?.method ?? 'GET', headers: opts?.headers ?? {}, body: opts?.body ?? null };
  const res = await fetch('/api/proxy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), credentials: 'include' });
  const text = await res.text();
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try { return JSON.parse(text); } catch (e) { return text; }
  }
  return text;
}

export default apiProxy;
