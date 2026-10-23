import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { access, mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const origin = process.env.T44_UI_URL ?? 'http://127.0.0.1:5176'
if (origin !== 'http://127.0.0.1:5176') throw new Error('This developer check is restricted to its own port 5176')
const output = resolve(process.env.T44_UI_OUTPUT ?? 'agents/frontend/logout-browser')
try { await access(resolve(output, 'results.json')); throw new Error('Refusing to overwrite existing results') } catch (error) { if (error.code !== 'ENOENT') throw error }
await mkdir(output, { recursive: true })
const credentials = JSON.parse(await readFile(process.env.T44_UI_CREDENTIALS, 'utf8')).manager
const evidence = { checkedAt: new Date().toISOString(), origin, operator: 'AI frontend developer', screenshots: [], layouts: [], checks: [], pageErrors: [], api: [], businessWrites: 0, controlActions: [] }
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
async function capture(page, name) {
  await page.evaluate(async () => { await document.fonts.ready; await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))); await Promise.all(document.getAnimations().filter(animation => animation.effect?.getComputedTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => {}))) })
  const file = name + '.png'; await page.screenshot({ path: resolve(output, file), animations: 'disabled' }); evidence.screenshots.push(file)
  evidence.layouts.push(await page.evaluate(label => ({ label, width: innerWidth, scrollWidth: document.documentElement.scrollWidth }), name))
}
async function login(page) {
  await page.locator('#login-username').fill(credentials.username); await page.locator('#login-password').fill(credentials.password)
  await page.locator('.login-submit').click(); await page.locator('.login-page').waitFor({ state: 'hidden' }); await page.locator('.business-card').first().waitFor()
  await page.locator('.data-state[aria-busy="true"]').waitFor({ state: 'hidden' })
}
async function assertCleared(page, name) {
  await page.locator('.login-page').waitFor()
  const state = await page.evaluate(projectName => ({ authenticatedShells: document.querySelectorAll('.app-shell').length, projectNameRetained: document.body.textContent.includes(projectName), cards: document.querySelectorAll('.business-card').length, overlays: document.querySelectorAll('.el-dialog,.el-drawer').length }), name)
  if (state.authenticatedShells || state.projectNameRetained || state.cards || state.overlays) throw new Error('Session content remains in rendered DOM: ' + JSON.stringify(state))
  return state
}
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', locale: 'zh-CN', timezoneId: 'Asia/Shanghai' })
    const page = await context.newPage(); let authorization = ''
    page.on('pageerror', error => evidence.pageErrors.push(error.message))
    page.on('request', request => { const path = new URL(request.url()).pathname; if (!path.startsWith('/api/v1/')) return; authorization = request.headers().authorization ?? authorization; if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && !['/api/v1/auth/login', '/api/v1/auth/logout'].includes(path)) evidence.businessWrites++ })
    page.on('response', async response => { const path = new URL(response.url()).pathname; if (path.startsWith('/api/v1/')) evidence.api.push({ width, method: response.request().method(), path, status: response.status(), requestId: response.headers()['x-request-id'] ?? null }) })
    await page.goto(origin + '/projects'); await login(page)
    const projectName = await page.locator('.project-picker select option:checked').textContent()
    if (!projectName?.trim()) throw new Error('No selected project name')
    const selectedName = projectName.trim()
    await capture(page, `${width}-signed-in`)
    if (width === 390) await page.getByRole('button', { name: '打开主导航', exact: true }).click()
    await page.getByRole('link', { name: '交付任务', exact: true }).click(); await page.locator('.business-card').first().waitFor()
    if (width === 390) await page.getByRole('button', { name: '关闭主导航', exact: true }).waitFor({ state: 'hidden' })
    const acknowledged = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/auth/logout' && response.request().method() === 'POST')
    await page.getByRole('button', { name: '退出', exact: true }).click(); const logoutResponse = await acknowledged
    if (logoutResponse.status() !== 200) throw new Error('Logout not acknowledged with 200')
    const logout = await assertCleared(page, selectedName); await capture(page, `${width}-logged-out`)
    await page.goBack(); const back = await assertCleared(page, selectedName); await capture(page, `${width}-back`)
    await page.reload(); const reload = await assertCleared(page, selectedName)
    await login(page)
    // Revoke only this browser's current synthetic session through the real endpoint, then let UI discover real 401.
    if (!authorization) throw new Error('No current browser authorization available for session-only revocation')
    const revoked = await context.request.post(origin + '/api/v1/auth/logout', { headers: { Authorization: authorization, Accept: 'application/json' } })
    evidence.controlActions.push({ width, method: 'POST', path: '/api/v1/auth/logout', status: revoked.status(), purpose: 'revoke this browser session without changing frontend memory' })
    if (revoked.status() !== 200) throw new Error('Synthetic session revocation failed')
    const unauthorized = page.waitForResponse(response => new URL(response.url()).pathname.startsWith('/api/v1/') && response.status() === 401)
    await page.getByRole('button', { name: '刷新记录', exact: true }).click(); await unauthorized
    const expired = await assertCleared(page, selectedName); await capture(page, `${width}-expired`)
    evidence.checks.push({ width, logout, back, reload, expired, logoutStatus: logoutResponse.status(), revokedOnlyCurrentSession: true })
    await context.close()
  }
  evidence.passed = !evidence.pageErrors.length && !evidence.businessWrites && evidence.layouts.every(item => item.scrollWidth <= item.width)
  if (!evidence.passed) process.exitCode = 1
} catch (error) { evidence.passed = false; evidence.failure = error.message; process.exitCode = 1 }
finally { await browser.close(); evidence.chromeClosedAt = new Date().toISOString(); await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n'); console.log(JSON.stringify(evidence)) }
