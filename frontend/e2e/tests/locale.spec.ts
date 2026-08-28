import { test, expect } from '@playwright/test';

const baseUrl = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3000';
const apiBaseUrl = process.env.PLAYWRIGHT_API_BASE_URL || 'http://127.0.0.1:8000';

test.describe('Locale persistence', () => {
  test('frontend persists selected locale to backend and hydrates on load', async ({ page, request }) => {
    // Assumes backend and frontend are running locally and share TENANT_ID
    const response = await page.goto(`${baseUrl}/settings`);
    if (!response || !response.ok()) {
      test.skip(true, 'Frontend app is not available at the configured base URL');
    }

    // Select Kiswahili
    await page.selectOption('select', 'sw');
    // Wait briefly for the client POST to /tenant/current/locale
    await page.waitForTimeout(500);

    // Verify backend persisted value via public API
    let resp;
    try {
      resp = await request.get(`${apiBaseUrl}/tenant/current`);
    } catch (error) {
      test.skip(true, 'Backend API is not available at the configured API base URL');
    }
    if (!resp || !resp.ok()) {
      test.skip(true, 'Backend API is not available at the configured API base URL');
    }
    const json = await resp.json();
    expect(json.preferred_locale).toBe('sw');

    // Reload the page and ensure UI locale reflects stored value
    await page.reload();
    const htmlLang = await page.evaluate(() => document.documentElement.lang);
    expect(htmlLang).toBe('sw');
  });
});
