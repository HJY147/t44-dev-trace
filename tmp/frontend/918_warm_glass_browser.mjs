import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const mode = process.argv[2] ?? 'prototype'
const output = resolve('agents/frontend/warm-glass-browser', mode)
await mkdir(output, { recursive: true })
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
const evidence = { mode, checkedAt: new Date().toISOString(), screenshots: [], layouts: [], pageErrors: [], checks: [] }
async function capture(page, name) {
  const file = `${name}.png`
  await page.screenshot({ path: resolve(output, file), fullPage: true })
  evidence.screenshots.push(file)
  evidence.layouts.push(await page.evaluate((label) => ({ label, width: innerWidth, scrollWidth: document.documentElement.scrollWidth, overflow: document.documentElement.scrollWidth > innerWidth }), name))
}
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' })
    const page = await context.newPage()
    page.on('pageerror', (error) => evidence.pageErrors.push(error.message))
    if (mode === 'prototype') {
      await page.goto(pathToFileURL(resolve('docs/ui/warm-glass/prototype.html')).href)
      await capture(page, `${width}-workspace`)
      await page.locator('#preview-detail').click()
      await capture(page, `${width}-detail`)
      await page.keyboard.press('Escape')
      await page.locator('#create').click()
      await page.locator('#sample-form button[type="submit"]').click()
      if (!await page.locator('#form-error').isVisible()) throw new Error('Prototype form error is hidden')
      await capture(page, `${width}-form-error`)
      await page.keyboard.press('Escape')
      await page.locator('.prototype-bar [data-screen="login"]').click()
      await capture(page, `${width}-login`)
      await page.locator('#sample-login button[type="submit"]').click()
      if (!await page.locator('#login-error').isVisible()) throw new Error('Prototype login error is hidden')
      await page.locator('#sample-user').fill('prototype-only')
      await page.locator('#sample-password').fill('not-a-credential')
      await page.locator('#sample-login button[type="submit"]').click()
      await page.locator('#filter').selectOption('blocked')
      if (await page.locator('.record:visible').count() !== 1) throw new Error('Prototype filter mismatch')
      evidence.checks.push({ width, loginNavigation: true, formError: true, filter: true, detailEscape: true })
    } else if (mode === 'live') {
      const credentials = JSON.parse(await readFile(process.env.T44_UI_CREDENTIALS, 'utf8'))
      const account = credentials.manager ?? credentials
      await page.goto(process.env.T44_UI_URL ?? 'http://127.0.0.1:5176/')
      await capture(page, `${width}-login`)
      await page.locator('#login-username').fill(account.username)
      await page.locator('#login-password').fill(account.password)
      await page.locator('.login-submit').click()
      await page.locator('.login-page').waitFor({ state: 'hidden' })
      await page.locator('.business-card').first().waitFor()
      await capture(page, `${width}-workspace`)
      await page.getByRole('button', { name: '登记交付任务', exact: true }).click()
      await page.locator('.operation-form button[type="submit"]').click()
      await page.locator('.operation-form .field-error').first().waitFor()
      await capture(page, `${width}-form-error`)
      await page.getByRole('button', { name: '取消', exact: true }).click()
      await page.locator('.business-card .text-button').first().click()
      await page.locator('.task-toolbar').waitFor()
      await capture(page, `${width}-detail`)
      await page.keyboard.press('Escape')
      evidence.checks.push({ width, realLogin: true, realTaskList: true, localFormError: true, realTaskDetail: true })
    } else throw new Error(`Unknown mode: ${mode}`)
    await context.close()
  }
  if (evidence.pageErrors.length || evidence.layouts.some((item) => item.overflow)) throw new Error('Page error or horizontal overflow observed')
  evidence.completed = true
} catch (error) {
  evidence.completed = false
  evidence.failure = error.message
  process.exitCode = 1
} finally {
  await browser.close()
  await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify(evidence))
}
