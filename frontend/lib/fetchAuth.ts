// This helper relies entirely on server-side HttpOnly cookies for auth.
// Client may optionally receive an access token in responses, but the
// canonical method is cookie-based session.

function clearTokens() {
  // no client-side token storage; function retained for compatibility
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const res = await fetch('/api/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, cache: 'no-store', credentials: 'include' });
    if (!res.ok) return null;
    const data = await res.json();
    const accessToken = data.accessToken ?? data.access_token ?? data.token ?? null;
    return accessToken;
  } catch (err) {
    return null;
  }
}

export async function fetchWithAuth(input: RequestInfo, init?: RequestInit, apiBase?: string) {
  const base = apiBase ?? (process.env.NEXT_PUBLIC_API_BASE_URL ?? '');
  const headers = new Headers(init?.headers || {});
  const url = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
  const finalUrl = url.startsWith('http') ? url : (base ? base.replace(/\/$/, '') : '') + (url.startsWith('/') ? url : '/' + url);
  // If finalUrl targets configured backend base, proxy through server so cookies are used.
  let res: Response;
  try {
    if (base && finalUrl.startsWith(base)) {
      // call server proxy
      const path = finalUrl.slice(base.length) || '/';
      const proxyBody = { path, method: init?.method ?? 'GET', headers: Object.fromEntries(headers.entries()), body: undefined as any };
      if (init?.body) {
        try {
          proxyBody.body = typeof init.body === 'string' ? JSON.parse(init.body) : init.body;
        } catch (e) {
          proxyBody.body = init.body;
        }
      }
      res = await fetch('/api/proxy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(proxyBody), cache: init?.cache ?? 'no-store', credentials: 'include' });
    } else {
      res = await fetch(finalUrl, { ...init, headers, cache: init?.cache ?? 'no-store', credentials: 'include' });
    }
  } catch (err) {
    throw err;
  }
  // If unauthorized, try refresh once via server endpoint and retry with returned token
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      return fetch(finalUrl, { ...init, headers, cache: init?.cache ?? 'no-store' });
    }
  }
  return res;
}

export { refreshAccessToken, clearTokens, fetchWithAuth as default };
