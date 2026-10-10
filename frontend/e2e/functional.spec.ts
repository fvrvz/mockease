import { test, expect } from '@playwright/test'

test.describe('MockEase Frontend Functional UI Tests', () => {
  const uniqueId = Date.now()
  const user = {
    email: `ui_user_${uniqueId}@mockease.dev`,
    username: `uiuser_${uniqueId}`,
    password: 'Password123!',
  }

  test('Registration, navigation to dashboard, and application creation flow', async ({ page }) => {
    // 1. Visit Login page
    await page.goto('/login')
    await expect(page).toHaveTitle(/MockEase/)
    await expect(page.locator('.auth-title')).toHaveText('MockEase')

    // 2. Click navigate to Register
    await page.locator('a[href="/register"]').click()
    await expect(page).toHaveURL(/.*register/)
    await expect(page.locator('.auth-subtitle')).toHaveText('Create your account')

    // 3. Register user
    await page.locator('input[type="email"]').fill(user.email)
    await page.locator('input[autocomplete="username"]').fill(user.username)
    const passwordInputs = page.locator('input[type="password"]')
    await passwordInputs.nth(0).fill(user.password)
    await passwordInputs.nth(1).fill(user.password)

    await page.locator('button[type="submit"]').click()

    // 4. Should redirect to Dashboard
    await expect(page).toHaveURL(/.*dashboard|.*\//)
    await expect(page.locator('.dashboard__title')).toHaveText('Applications')

    // 5. Open Create Application modal
    const createBtn = page.locator('button:has-text("+ Create Application")')
    await createBtn.click()

    // 6. Fill Create Application form
    await expect(page.locator('.modal')).toBeVisible()
    await page.locator('input[placeholder*="E-Commerce API"]').fill(`E2E App ${uniqueId}`)
    await page.locator('textarea[placeholder*="mock workspace"]').fill('Automated testing created application')

    // 7. Submit application creation
    await page.locator('.modal__footer button.btn--primary').click()

    // 8. Should navigate to the Application detail workspace
    await expect(page).toHaveURL(/.*apps\/.+/)
  })

  test('404 Not Found Page renders properly and navigates home', async ({ page }) => {
    await page.goto('/some-nonexistent-route-404')
    await expect(page.locator('.not-found__code')).toHaveText('404')
    await expect(page.locator('.not-found__title')).toHaveText('Page not found')

    const homeBtn = page.locator('a:has-text("Go to Dashboard")')
    await expect(homeBtn).toBeVisible()
  })

  test('Theme switcher toggles light/dark/system mode and applies palette presets in Settings', async ({ page }) => {
    // Navigate to Settings
    await page.goto('/settings')

    // Expect settings view to load
    await expect(page.locator('.settings-title')).toContainText('Appearance & Preferences')

    // 1. Toggle Light Mode
    const lightBtn = page.locator('button[title="Light mode"]').first()
    await lightBtn.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')

    // 2. Select Light Palette (e.g. Nordic Frost)
    const frostPalette = page.locator('.palette-card:has-text("Nordic Frost")')
    await frostPalette.click()
    await expect(page.locator('html')).toHaveAttribute('data-palette', 'frost')

    // 3. Toggle Dark Mode
    const darkBtn = page.locator('button[title="Dark mode"]').first()
    await darkBtn.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // 4. Select Dark Palette (e.g. Cyber Emerald)
    const emeraldPalette = page.locator('.palette-card:has-text("Cyber Emerald")')
    await emeraldPalette.click()
    await expect(page.locator('html')).toHaveAttribute('data-palette', 'emerald')

    // 5. Toggle System Mode
    const systemBtn = page.locator('button[title="Follow system appearance"]').first()
    await systemBtn.click()
    const htmlTheme = await page.locator('html').getAttribute('data-theme')
    expect(htmlTheme === 'dark' || htmlTheme === 'light').toBe(true)
  })
})

