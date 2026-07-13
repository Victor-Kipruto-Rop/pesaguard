import { test, expect } from '@playwright/test';

test.describe('Locale persistence', () => {
  test('frontend persists selected locale to backend and hydrates on load', async ({ page, request }) => {
    // Assumes backend and frontend are running locally and share TENANT_ID
    await page.goto('/settings');

    // Select Kiswahili
    await page.selectOption('select', 'sw');
    // Wait briefly for the client POST to /tenant/current/locale
    await page.waitForTimeout(500);

    // Verify backend persisted value via public API
    const resp = await request.get('/tenant/current');
    expect(resp.ok()).toBeTruthy();
    const json = await resp.json();
    expect(json.preferred_locale).toBe('sw');

    // Reload the page and ensure UI locale reflects stored value
    await page.reload();
    const htmlLang = await page.evaluate(() => document.documentElement.lang);
    expect(htmlLang).toBe('sw');
  });
});
