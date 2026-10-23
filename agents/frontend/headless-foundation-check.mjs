import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const directory = dirname(fileURLToPath(import.meta.url))
const screenshots = join(directory, 'screenshots')
await mkdir(screenshots, { recursive: true })
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const errors = []
const businessRequests = []
const results = []
try {
  for (const [name, viewport] of [['desktop', { width: 1440, height: 1000 }], ['mobile', { width: 390, height: 844 }]]) {
    const page = await browser.newPage({ viewport, locale: 'zh-CN', timezoneId: 'Asia/Shanghai', reducedMotion: 'reduce' })
    page.on('pageerror', (error) => errors.push(error.message))
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
    page.on('request', (request) => { if (new URL(request.url()).pathname.startsWith('/api/')) businessRequests.push(request.url()) })
    await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle' })
    await page.getByRole('heading', { level: 1, name: '工作台', exact: true }).waitFor()
    assert.equal(await page.locator('.metric-card__value').count(), 4)
    assert.deepEqual(await page.locator('.metric-card__value').allTextContents(), ['—', '—', '—', '—'])
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
    assert.equal(overflow, false, name + ' page horizontal overflow')
    await page.screenshot({ path: join(screenshots, name + '.png'), fullPage: true })
    if (name === 'desktop') {
      await page.keyboard.press('Tab')
      assert.equal(await page.evaluate(() => document.activeElement?.textContent), '跳转到主要内容')
      await page.getByRole('navigation', { name: '主导航' }).getByRole('link', { name: '交付任务', exact: true }).click()
      await page.getByRole('heading', { level: 1, name: '交付任务', exact: true }).waitFor()
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'page-heading')
      assert.equal(await page.getByRole('button', { name: '登记任务，连接后可用' }).isDisabled(), true)
      await page.goto('http://127.0.0.1:4173/unknown-page', { waitUntil: 'networkidle' })
      await page.getByRole('heading', { level: 1, name: '页面不存在' }).waitFor()
    } else {
      await page.getByRole('button', { name: '打开主导航' }).click()
      const drawer = page.getByRole('dialog', { name: '主导航' })
      await drawer.getByRole('link', { name: '迭代排期', exact: true }).click()
      await page.getByRole('heading', { level: 1, name: '迭代排期', exact: true }).waitFor()
      await page.getByRole('button', { name: '打开主导航' }).click()
      await page.getByRole('button', { name: '关闭主导航' }).click()
      await drawer.waitFor({ state: 'hidden' })
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false)
    }
    results.push({ name, viewport, screenshot: 'agents/frontend/screenshots/' + name + '.png', layoutAndNavigation: 'passed' })
    await page.close()
  }
  assert.deepEqual(errors, [])
  assert.deepEqual(businessRequests, [])
  const result = { browser: 'installed Chrome in headless mode', module: 'frontend foundation only; no API integration or business acceptance', results, errors, businessRequests }
  await writeFile(join(directory, 'headless-foundation-result.json'), JSON.stringify(result, null, 2) + '\n')
  console.log(JSON.stringify(result, null, 2))
} finally { await browser.close() }
