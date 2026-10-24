import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { access, mkdir, readFile, stat, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'

const origin = 'http://127.0.0.1:5178', output = resolve(process.env.T44_UI_OUTPUT ?? 'agents/frontend/native-user-preview-first')
const adapterPath = process.env.T44_UI_CREDENTIALS
if (!adapterPath || ((await stat(adapterPath)).mode & 0o777) !== 0o600) throw new Error('Private ordinary credential adapter must be0600')
const credentials = JSON.parse(await readFile(adapterPath, 'utf8')).manager
try { await access(resolve(output, 'results.json')); throw new Error('Refusing result overwrite') } catch (error) { if (error.code !== 'ENOENT') throw error }
await mkdir(output, { recursive: true })
const clean = value => String(value).replaceAll(credentials.username, '[redacted-account]').replaceAll(credentials.password, '[redacted-password]').replace(/Bearer\s+\S+/gi, 'Bearer [redacted]').replace(/([?&](?:token|password|username)=)[^&\s]+/gi, '$1[redacted]')
const hash = value => createHash('sha256').update(value).digest('hex')
const bindingFile = 'agents/deployment/native-bounded-demo-validation/user-demo-operational-binding.json'
const bindingText = await readFile(bindingFile, 'utf8'), binding = JSON.parse(bindingText)
if (binding.application_source !== 'bc5aef9c62393134582affb7a690acb33ac2b833' || binding.source_files_verified !== 92) throw new Error('Unexpected published source binding')
function protectedListeners() {
  return Object.fromEntries([5173, 18080, 5175, 18084, 5176, 18089, 13306, 5177, 18086].map(port => {
    const sockets = spawnSync('lsof', ['-nP', '-t', `-iTCP:${port}`, '-sTCP:LISTEN'], { encoding: 'utf8' })
    if (![0, 1].includes(sockets.status)) throw new Error('Listener observation failed')
    const pids = [...new Set(sockets.stdout.trim().split(/\s+/).filter(Boolean))].sort((a, b) => Number(a) - Number(b))
    const ps = pids.length ? spawnSync('ps', ['-p', pids.join(','), '-o', 'uid=,pid=,ppid=,pgid=,lstart='], { encoding: 'utf8' }) : { status: 0, stdout: '' }
    if (ps.status !== 0) throw new Error('Listener identity observation failed')
    return [port, ps.stdout.trim().split('\n').filter(Boolean).map(line => line.trim().replace(/\s+/g, ' ')).sort()]
  }))
}
const evidence = { operator: 'AI frontend developer', startedAt: new Date().toISOString(), origin, apiProxy: 'http://127.0.0.1:18088', applicationSource: binding.application_source, sourceBinding: { file: bindingFile, sha256: hash(bindingText), sourceFilesVerifiedByDeploymentOwner: 92, sourceIdentityLimit: 'Published deployment/root binding, not this browser independently hashing live source or process memory.' }, attempt: 1, credentialAdapterMode: '0600', requestLimit: 80, requests: [], responses: [], console: [], pageErrors: [], requestFailures: [], blockedRequests: [], views: [], screenshots: [], logouts: [], businessMutations: 0, beforeProtected: protectedListeners() }
let browser, reads = 0
async function stable(page) {
  await page.locator('.data-state[aria-busy="true"]').waitFor({ state: 'hidden' })
  await page.evaluate(async () => { await document.fonts.ready; await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))); await Promise.all(document.getAnimations().filter(animation => animation.effect?.getComputedTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => {}))) })
}
async function capture(page, width, label) {
  await stable(page)
  const file = `${width}-${label}.png`
  await page.screenshot({ path: resolve(output, file), animations: 'disabled', mask: [page.locator('.account')] })
  evidence.screenshots.push(file)
  evidence.views.push(await page.evaluate(({ width, label }) => ({ width, label, path: location.pathname, scrollWidth: document.documentElement.scrollWidth, cards: document.querySelectorAll('.business-card').length, heading: document.querySelector('h1')?.textContent?.trim(), notificationStatistics: document.querySelector('[aria-label="通知统计"]')?.textContent?.trim() ?? null }), { width, label }))
}
async function navigate(page, width, label, route, apiPattern) {
  const pending = page.waitForResponse(response => apiPattern.test(new URL(response.url()).pathname) && response.request().method() === 'GET')
  if (width < 800) await page.getByRole('button', { name: '打开主导航', exact: true }).click()
  const navigation = width < 800 ? page.locator('.mobile-navigation:visible nav') : page.locator('.sidebar nav')
  await navigation.getByRole('link', { name: label, exact: true }).click()
  await page.waitForURL(origin + route)
  const response = await pending
  if (response.status() !== 200) throw new Error(label + ' read HTTP' + response.status())
  await stable(page)
}
try {
  browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', locale: 'zh-CN', timezoneId: 'Asia/Shanghai' }), page = await context.newPage()
    page.on('console', message => evidence.console.push({ width, type: message.type(), text: clean(message.text()).slice(0, 500) }))
    page.on('pageerror', error => evidence.pageErrors.push({ width, message: clean(error.message) }))
    page.on('request', request => { const url = new URL(request.url()); if (url.pathname.startsWith('/api/v1/')) evidence.requests.push({ width, method: request.method(), path: url.pathname }) })
    page.on('response', response => { const url = new URL(response.url()); if (url.pathname.startsWith('/api/v1/')) evidence.responses.push({ width, method: response.request().method(), path: url.pathname, status: response.status(), requestId: response.headers()['x-request-id'] ?? null }) })
    page.on('requestfailed', request => evidence.requestFailures.push({ width, method: request.method(), path: new URL(request.url()).pathname, error: clean(request.failure()?.errorText ?? '') }))
    await page.route('**/api/v1/**', async route => {
      const request = route.request(), url = new URL(request.url()), method = request.method()
      const authentication = method === 'POST' && ['/api/v1/auth/login', '/api/v1/auth/logout'].includes(url.pathname)
      if (method === 'GET') reads++
      if (url.origin !== origin || !['GET', 'HEAD', 'OPTIONS'].includes(method) && !authentication || reads > evidence.requestLimit) {
        if (!authentication && !['GET', 'HEAD', 'OPTIONS'].includes(method)) evidence.businessMutations++
        evidence.blockedRequests.push({ width, method, path: url.pathname, reason: reads > evidence.requestLimit ? 'Read bound exceeded' : 'Outside read/session scope' })
        await route.abort(); return
      }
      await route.continue()
    })
    try {
      await page.goto(origin)
      await page.locator('#login-username').fill(credentials.username); await page.locator('#login-password').fill(credentials.password)
      await page.locator('.login-submit').click(); await page.locator('.login-page').waitFor({ state: 'hidden' }); await page.locator('.business-card').first().waitFor(); await stable(page)
      const picker = page.locator('.project-picker select'), choices = await picker.locator('option').evaluateAll(options => options.map(option => ({ value: option.value, disabled: option.disabled })).filter(option => /^\d+$/.test(option.value) && !option.disabled))
      if (!choices.length) throw new Error('No existing ordinary project available')
      const selected = choices.at(-1).value, previous = await picker.inputValue()
      if (selected !== previous) { const pending = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/projects/${selected}/tasks` && response.request().method() === 'GET'); await picker.selectOption(selected); if ((await pending).status() !== 200) throw new Error('Project switch read failed') }
      await stable(page); evidence.views.push({ width, label: 'project-selection', projectId: Number(selected), selectableExistingProjects: choices.length })
      await navigate(page, width, '交付任务', '/tasks', new RegExp(`/api/v1/projects/${selected}/tasks$`)); if (!await page.locator('.business-card').count()) throw new Error('Expected existing task cards'); await capture(page, width, 'tasks')
      await navigate(page, width, '通知中心', '/notifications', /\/api\/v1\/me\/notifications$/); await page.getByRole('status', { name: '通知统计', exact: true }).waitFor(); await capture(page, width, 'notifications')
      await navigate(page, width, '审计记录', '/audit', new RegExp(`/api/v1/projects/${selected}/audit-events$`)); await capture(page, width, 'audit')
      const logout = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1/auth/logout' && response.request().method() === 'POST'); await page.getByRole('button', { name: '退出', exact: true }).click(); const result = await logout; await page.locator('.login-page').waitFor()
      if (result.status() !== 200 || await page.locator('.app-shell').count()) throw new Error('Normal logout did not clear authenticated shell')
      evidence.logouts.push({ width, status: result.status(), loginFormVisible: true, authenticatedShellAbsent: true })
    } finally { await context.close() }
  }
  evidence.passed = !evidence.pageErrors.length && !evidence.requestFailures.length && !evidence.blockedRequests.length && !evidence.businessMutations && evidence.responses.every(response => response.status === 200) && evidence.logouts.length === 2 && evidence.views.filter(view => view.scrollWidth !== undefined).every(view => view.scrollWidth <= view.width)
  if (!evidence.passed) process.exitCode = 1
} catch (error) { evidence.passed = false; evidence.failure = clean(error.message); process.exitCode = 1 }
finally {
  if (browser) await browser.close()
  evidence.afterProtected = protectedListeners(); evidence.protectedListenerIdentitiesUnchanged = JSON.stringify(evidence.beforeProtected) === JSON.stringify(evidence.afterProtected)
  evidence.getRequestCount = reads; evidence.finishedAt = new Date().toISOString(); evidence.browserClosed = true
  if (!evidence.protectedListenerIdentitiesUnchanged) { evidence.passed = false; process.exitCode = 1 }
  await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n'); console.log(JSON.stringify(evidence))
}
