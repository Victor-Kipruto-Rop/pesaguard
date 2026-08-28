/**
 * Minimal Node script to perform an integration smoke test:
 * 1) POST credentials to `/api/auth/login` (server proxy)
 * 2) GET a proxied backend endpoint via `/api/proxy` and assert 200
 *
 * Configure `NEXT_PUBLIC_BASE_URL` if running outside dev server.
 */

const fetch = globalThis.fetch || require('node-fetch');

async function run() {
  const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
  console.log('Using base', base);

  // 1) login
  const loginRes = await fetch(`${base}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: process.env.TEST_EMAIL || 'test@example.com', password: process.env.TEST_PASSWORD || 'password' }),
  });
  console.log('login status', loginRes.status);
  if (!loginRes.ok) throw new Error('login failed');

  // capture cookies
  const cookies = loginRes.headers.raw ? (loginRes.headers.raw()['set-cookie'] || []) : (loginRes.headers.get('set-cookie') ? [loginRes.headers.get('set-cookie')] : []);
  console.log('got cookies', cookies.length);

  // 2) request proxied backend endpoint (example: /api/health) via /api/proxy
  const proxyRes = await fetch(`${base}/api/proxy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Cookie: cookies.join('; ') },
    body: JSON.stringify({ path: '/api/health', method: 'GET' }),
  });
  console.log('proxy status', proxyRes.status);
  if (!proxyRes.ok) throw new Error('proxy request failed');

  const text = await proxyRes.text();
  console.log('proxy response:', text.slice(0, 200));
  console.log('E2E smoke test passed');
}

run().catch((e) => { console.error(e); process.exit(1); });
