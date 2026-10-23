import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const mode = process.argv[2] ?? 'prototype'
const output = resolve('agents/frontend/warm-glass-browser', process.env.T44_UI_PHASE ?? mode)
await mkdir(output, { recursive: true })
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
const evidence = { mode, checkedAt: new Date().toISOString(), screenshots: [], layouts: [], pageErrors: [], checks: [], api: [] }
async function capture(page, name) {
  const file = `${name}.png`
  await page.evaluate(async () => {
    await document.fonts.ready
    await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))
    await Promise.all(document.getAnimations().filter((animation) => animation.effect?.getComputedTiming().iterations !== Infinity).map((animation) => animation.finished.catch(() => undefined)))
  })
  await page.screenshot({ path: resolve(output, file), fullPage: mode === 'prototype', animations: 'disabled' })
  evidence.screenshots.push(file)
  evidence.layouts.push(await page.evaluate((label) => ({ label, width: innerWidth, scrollWidth: document.documentElement.scrollWidth, overflow: document.documentElement.scrollWidth > innerWidth }), name))
}
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' })
    const page = await context.newPage()
    page.on('pageerror', (error) => evidence.pageErrors.push(error.message))
    page.on('response', (response) => { const url = new URL(response.url()); if (url.pathname.startsWith('/api/v1/')) evidence.api.push({ method: response.request().method(), path: url.pathname, status: response.status() }) })
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
      const loginFocus = await page.locator('#login-username').evaluate((element) => ({ focused: document.activeElement === element, outline: getComputedStyle(element).outlineStyle, outlineWidth: getComputedStyle(element).outlineWidth }))
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
      await page.locator('.el-dialog__body').evaluate((element) => { element.scrollTop = 0 })
      await capture(page, `${width}-form-error`)
      const dialogBody = page.locator('.el-dialog__body')
      await dialogBody.evaluate((element) => { element.scrollTop = element.scrollHeight })
      await page.getByRole('button', { name: '取消', exact: true }).focus()
      await capture(page, `${width}-form-bottom`)
      const formScroll = await dialogBody.evaluate((element) => ({ clientHeight: element.clientHeight, scrollHeight: element.scrollHeight, scrollTop: element.scrollTop, atBottom: Math.abs(element.scrollHeight - element.clientHeight - element.scrollTop) <= 2 }))
      if (!formScroll.atBottom) throw new Error('Form content did not reach its bottom')
      const formCloseVisible = await page.locator('.el-dialog__headerbtn').evaluate((element) => { const box = element.getBoundingClientRect(); return box.top >= 0 && box.bottom <= innerHeight })
      if (!formCloseVisible) throw new Error('Form close button is outside viewport')
      await page.getByRole('button', { name: '取消', exact: true }).click()
      await page.locator('.business-card .text-button').first().click()
      await page.locator('.task-toolbar').waitFor()
      await page.locator('.el-drawer:visible .record-detail').first().waitFor()
      await capture(page, `${width}-detail`)
      await page.getByRole('tab', { name: '变更与排期差异', exact: true }).click()
      await page.locator('.task-toolbar').waitFor()
      await page.locator('.el-drawer__body').last().evaluate((element) => { element.scrollTop = element.scrollHeight })
      await capture(page, `${width}-detail-audit`)
      await page.getByRole('tab', { name: '任务概览', exact: true }).click()
      await page.locator('.el-drawer:visible .record-detail').first().waitFor()
      await page.locator('.el-drawer__body').last().evaluate((element) => { element.scrollTop = element.scrollHeight })
      await capture(page, `${width}-detail-bottom`)
      await page.keyboard.press('Escape')
      if (width === 390) await page.getByRole('button', { name: '打开主导航', exact: true }).click()
      await page.getByRole('link', { name: '通知中心', exact: true }).click()
      await page.getByRole('status', { name: '通知统计', exact: true }).waitFor()
      const notificationCounts = await page.getByRole('status', { name: '通知统计', exact: true }).innerText()
      await capture(page, `${width}-notifications`)
      const cdp = await context.newCDPSession(page)
      await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }, { name: 'prefers-reduced-transparency', value: 'reduce' }] })
      const reducedTransparency = await page.evaluate(() => matchMedia('(prefers-reduced-transparency: reduce)').matches)
      if (!reducedTransparency) throw new Error('Reduced transparency emulation is unavailable')
      await capture(page, `${width}-reduced-transparency`)
      evidence.checks.push({ width, realLogin: true, loginFocus, realTaskList: true, localFormError: true, formCloseVisible, formScroll, realTaskDetail: true, taskAuditTab: true, taskDetailBottom: true, notificationCounts, reducedTransparency })
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
