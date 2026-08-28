// Simple e2e script: POST /api/auth/login then GET /api/notifications
// Run: node frontend/scripts/e2e-login-notifications-test.js --base=http://localhost:3000

const base = (process.argv.find(a => a.startsWith('--base=')) || '--base=http://localhost:3000').split('=')[1];
(async function() {
  try {
    const loginRes = await fetch(base + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
    });
    if (!loginRes.ok) {
      console.error('Login failed', loginRes.status);
      process.exit(2);
    }
    const loginData = await loginRes.json();
    const token = loginData.accessToken || loginData.access_token || loginData.token;
    if (!token) {
      console.error('No token returned from login');
      process.exit(3);
    }
    console.log('Login success, token received (redacted):', token.slice(0,6) + '...');

    const notifRes = await fetch(base + '/api/notifications', { headers: { Authorization: 'Bearer ' + token } });
    if (!notifRes.ok) {
      console.error('Notifications fetch failed', notifRes.status);
      process.exit(4);
    }
    const notifs = await notifRes.json();
    console.log('Fetched notifications:', Array.isArray(notifs) ? notifs.length : typeof notifs);
    console.log('Sample:', JSON.stringify((Array.isArray(notifs) ? notifs.slice(0,3) : notifs), null, 2));
  } catch (err) {
    console.error('Error', err);
    process.exit(1);
  }
})();
