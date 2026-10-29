import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const origin = process.env.T44_UI_URL ?? 'http://127.0.0.1:5173'
const output = resolve(process.env.T44_UI_OUTPUT ?? 'agents/coordinator/demo-preview')
const credentials = JSON.parse(await readFile(process.env.T44_UI_CREDENTIALS, 'utf8')).manager
await mkdir(output, { recursive: true })
const evidence = { checkedAt: new Date().toISOString(), origin, layouts: [], errors: [], failedResponses: [], screenshots: [], apiRequests: [], businessMutations: 0 }
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' })
    const page = await context.newPage()
    page.on('request', (request) => {
      const path = new URL(request.url()).pathname
      if (!path.startsWith('/api/v1/')) return
      evidence.apiRequests.push({ method: request.method(), path })
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && path !== '/api/v1/auth/login') evidence.businessMutations += 1
    })
    page.on('pageerror', (error) => evidence.errors.push(error.message))
    page.on('response', (response) => {
      if (response.status() >= 400) evidence.failedResponses.push({ path: new URL(response.url()).pathname, status: response.status() })
    })
    await page.goto(origin)
    await page.locator('#login-username').waitFor()
    await page.screenshot({ path: resolve(output, `${width}-login.png`), animations: 'disabled' })
    evidence.screenshots.push(`${width}-login.png`)
    await page.locator('#login-username').fill(credentials.username)
    await page.locator('#login-password').fill(credentials.password)
    await page.locator('.login-submit').click()
    await page.locator('.login-page').waitFor({ state: 'hidden' })
    await page.locator('.business-card').first().waitFor()
    await page.locator('.data-state[aria-busy="true"]').waitFor({ state: 'hidden' })
    await page.screenshot({ path: resolve(output, `${width}-workspace.png`), animations: 'disabled' })
    evidence.screenshots.push(`${width}-workspace.png`)
    evidence.layouts.push(await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth, cards: document.querySelectorAll('.business-card').length })))
    await context.close()
  }
  evidence.passed = !evidence.errors.length && !evidence.failedResponses.length && !evidence.businessMutations && evidence.layouts.every((item) => item.scrollWidth <= item.width && item.cards > 0)
  if (!evidence.passed) process.exitCode = 1
} catch (error) {
  evidence.passed = false
  evidence.failure = error.message
  process.exitCode = 1
} finally {
  await browser.close()
  await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify(evidence))
}
