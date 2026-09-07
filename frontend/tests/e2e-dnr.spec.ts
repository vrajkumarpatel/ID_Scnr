import { test, expect } from '@playwright/test'

test('DNR page lists entries and supports search', async ({ page }) => {
  await page.route('**/dnr', route => route.fulfill({ body: JSON.stringify([
    { id: 10, first_name: 'Alice', last_name: 'Brown', dob: '1990-01-01', id_number: 'AB123', notes: 'Test', created_at: new Date().toISOString() }
  ]) }))
  await page.goto('/')
  await page.getByRole('button', { name: 'Do Not Rent' }).click()
  await expect(page.getByRole('heading', { name: 'Do Not Rent' })).toBeVisible()
  await expect(page.getByText('Alice Brown')).toBeVisible()
  await page.getByPlaceholder('Search name / ID').fill('Alice')
  await page.getByRole('button', { name: 'Refresh' }).click()
  await expect(page.getByText('Alice Brown')).toBeVisible()
})

test('Guests keyboard shortcuts: Ctrl+D sets date to today', async ({ page }) => {
  const today = new Date().toISOString().slice(0, 10)
  await page.route('**/guests?**', route => route.fulfill({ body: JSON.stringify([]) }))
  await page.route('**/stats/mtd?**', route => route.fulfill({ body: JSON.stringify({ mtd: 0 }) }))
  await page.goto('/')
  await page.keyboard.press('Control+D')
  await expect(page.locator('input[type="date"]')).toHaveValue(today)
})