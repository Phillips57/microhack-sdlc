import { expect, test } from '@playwright/test';

test.describe('Shopping cart', () => {
  test('shows an error when adding a product fails', async ({ page }) => {
    await page.route('**/api/cart/*/items', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: { message: 'Product not found' } }),
        });
        return;
      }

      await route.continue();
    });

    await page.goto('/products');
    await page.getByRole('button', { name: 'Increase quantity of SmartFeeder One' }).click();
    await page.getByRole('button', { name: 'Add 1 SmartFeeder One to cart' }).click();

    await expect(page.getByRole('alert')).toHaveText('Product not found');
  });

  test('add, update, and remove products with persisted totals', async ({ page }) => {
    await page.goto('/products');

    await page.getByRole('button', { name: 'Increase quantity of SmartFeeder One' }).click();
    await page.getByRole('button', { name: 'Add 1 SmartFeeder One to cart' }).click();
    await expect(page.getByRole('link', { name: 'Shopping cart, 1 items' })).toBeVisible();

    await page.reload();
    await page.getByRole('link', { name: 'Shopping cart, 1 items' }).click();
    await expect(page.getByRole('heading', { name: 'Your Cart' })).toBeVisible();
    await expect(page.getByText('Total: $97.49', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Increase quantity of SmartFeeder One' }).click();
    await expect(page.getByText('Total: $194.98', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Remove SmartFeeder One from cart' }).click();
    await expect(page.getByText('Your cart is empty.')).toBeVisible();
  });
});
