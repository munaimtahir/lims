import { test, expect } from '@playwright/test'

test('homepage has title', async ({ page }) => {
  await page.goto('/')
  
  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Vite/)
})

test('homepage has heading', async ({ page }) => {
  await page.goto('/')
  
  // Expects page to have a heading
  const heading = page.getByRole('heading', { level: 1 })
  await expect(heading).toBeVisible()
})
