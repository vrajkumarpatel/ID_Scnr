import { test, expect } from '@playwright/test'

test('Guests list, select, save, mark DNR', async ({ page }) => {
  await page.route('**/guests?**', route => route.fulfill({ body: JSON.stringify([
    { id: 1, first_name: 'John', last_name: 'Doe', room_number: '101', created_at: new Date().toISOString(), remarks: '' }
  ]) }))
  await page.route('**/stats/mtd?**', route => route.fulfill({ body: JSON.stringify({ mtd: 1 }) }))
  await page.route('**/guest/1', route => route.fulfill({ body: JSON.stringify({ id: 1, first_name: 'John', last_name: 'Doe' }) }))
  await page.route('**/guest/1/history', route => route.fulfill({ body: JSON.stringify([]) }))
  await page.route('**/guest/1/summary', route => route.fulfill({ body: JSON.stringify({ total_checkins: 1 }) }))
  await page.route('**/guest/1/update', route => route.fulfill({ body: JSON.stringify({ id: 1, remarks: 'DNR' }) }))
  await page.route('**/pms/write?**', route => route.fulfill({ body: JSON.stringify({ status: 'ok' }) }))

  await page.goto('/')
  await expect(page.getByText('John Doe')).toBeVisible()
  await page.getByText('John Doe').click()
  await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Mark DNR' }).click()
  await expect(page.getByText('Marked as DNR')).toBeVisible()
  await expect(page.getByRole('cell', { name: 'DNR' })).toBeVisible()
  await page.getByRole('button', { name: 'Save & Write to PMS' }).click()
  await expect(page.getByText('Written to PMS')).toBeVisible()
})

test('Settings save with mocked backend', async ({ page }) => {
  await page.route('**/settings/get', route => route.fulfill({ body: JSON.stringify({ ocr_provider: 'google', scan_device: '', auto_pms_write: false, dark_mode: true, pms_export_mode: 'json' }) }))
  await page.route('**/scan/devices', route => route.fulfill({ body: JSON.stringify({ devices: ['Scanner A'] }) }))
  await page.route('**/stats/mtd?**', route => route.fulfill({ body: JSON.stringify({ mtd: 5 }) }))
  await page.route('**/stats/dnr?**', route => route.fulfill({ body: JSON.stringify({ strong_hits: 2, overrides: 1, series: [] }) }))
  await page.route('**/admin/overrides?**', route => route.fulfill({ body: JSON.stringify([]) }))
  await page.route('**/settings/update', async route => {
    const body = JSON.stringify({ status: 'ok', settings: { ocr_provider: 'tesseract', scan_device: 'Scanner A', auto_pms_write: true, dark_mode: false, pms_export_mode: 'json' } })
    await route.fulfill({ body })
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Settings' }).click()
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  await page.getByRole('button', { name: /Save Settings/i }).click()
  await expect(page.getByText('Settings saved')).toBeVisible()
})