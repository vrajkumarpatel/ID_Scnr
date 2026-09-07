import { test, expect } from '@playwright/test'

test('homepage renders header and guests controls', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /IDscnr/i })).toBeVisible()
  await expect(page.getByRole('button', { name: /Today's Check-Ins/i })).toBeVisible()
  await expect(page.getByPlaceholder('Search name, room, ID')).toBeVisible()
})