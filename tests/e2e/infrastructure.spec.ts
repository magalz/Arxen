import { expect, test } from '@playwright/test';

test('the production web build opens in a browser', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveTitle('Arxen');
  await expect(page.getByRole('heading', { name: 'Arxen', level: 1 })).toBeVisible();
  await expect(page.getByText('Ambiente de desenvolvimento')).toBeVisible();
});

test('the API process answers HTTP with its health contract', async ({ request }) => {
  const response = await request.get('http://127.0.0.1:8000/healthz');

  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: 'ok', service: 'arxen-api' });
});
