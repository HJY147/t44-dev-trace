import assert from 'node:assert/strict'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { gzipSync, gunzipSync } from 'node:zlib'
import { createHash } from 'node:crypto'
import { resolve } from 'node:path'
import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'

// Developer UI equivalence probe: every API request is intercepted with synthetic data.
const phase = process.argv[2] ?? 'before'
assert.ok(['before', 'after'].includes(phase))
const base = resolve('agents/frontend/final-20261029')
const output = resolve(base, `ui-${phase}`)
await mkdir(output, { recursive: true })
const frozen = JSON.parse(await readFile('specs/contracts/openapi.json', 'utf8'))
const user = { id: 1, username: 'synthetic-ui-user', display_name: '合成界面用户' }
const project = { id: 1, name: '合成界面项目', description: '仅浏览器夹具，无真实后端', version: 1, my_roles: [1, 2, 3] }
const plan = { planned_start: '2026-10-29T00:00:00Z', planned_end: '2026-10-30T00:00:00Z', estimated_hours: 8, buffer_hours: 0, delay_contingency: '' }
const task = { id: 1, title: '合成交付任务', description: '用于样式与交互等价核对', project_id: 1, iteration_id: 1, owner_id: 1, version: 1, state: 2, plan, schedule_version: 1, block_reason: null }
const member = { user, project_id: 1, roles: [1, 2, 3], version: 1, active: true }
const iteration = { id: 1, project_id: 1, version: 1, plan: { ...plan, name: '合成迭代', capacity: [{ user_id: 1, available_hours: 8 }] } }
const template = frozen.components.schemas.ReviewTemplate.examples[0]
const names = { task_states: 'TaskState', project_roles: 'ProjectRole', transition_actions: 'TransitionAction', responsibility_stages: 'ResponsibilityStage', review_judgments: 'ReviewItemJudgment', review_verdicts: 'ReviewVerdict', risk_perspectives: 'RiskPerspective', risk_severities: 'RiskSeverity', escalation_levels: 'EscalationLevel', assessment_statuses: 'AssessmentStatus', audit_outcomes: 'AuditOutcome' }
const dictionaries = Object.fromEntries(Object.entries(names).map(([key, name]) => [key, (frozen.components.schemas[name].enum ?? [1, 2, 3]).map((value, index) => ({ value, name: frozen.components.schemas[name]['x-enum-names']?.[index] ?? `fixture_${value}`, label: `合成选项${value}` }))]))
const pageData = (items) => ({ items, total: items.length, page: 1, page_size: 20 })
const envelope = (data) => ({ data, meta: { replayed: false, request_id: 'synthetic-ui-request', contract_version: frozen.info.version, server_time: '2026-10-29T00:00:00Z', original_request_id: null } })
const evidence = { phase, startedAt: new Date().toISOString(), fixtureOnly: true, requests: [], pageErrors: [], checks: [], screenshots: [], differences: [] }
const snapshots = {}
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
async function capture(page, width, state) {
  await page.mouse.move(0, 0)
  await page.evaluate(async () => { await document.fonts.ready; await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))) })
  const key = `${width}-${state}`
  const computedNodes = await page.evaluate(() => {
    const style = (node, pseudo = null) => {
      const computed = getComputedStyle(node, pseudo)
      return Object.fromEntries([...computed].map(name => [name, computed.getPropertyValue(name)]))
    }
    return [...document.querySelectorAll('body *')].map(node => {
      const rect = node.getBoundingClientRect()
      return { tag: node.tagName, id: node.id, class: node.className?.baseVal ?? node.className, rect: [rect.x, rect.y, rect.width, rect.height], style: style(node), before: style(node, '::before'), after: style(node, '::after') }
    })
  })
  const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex')
  snapshots[key] = computedNodes.map(({ style, before, after, ...node }) => ({ ...node, style: hash(style), before: hash(before), after: hash(after) }))
  const layout = await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth }))
  assert.ok(layout.scrollWidth <= width, `${key} horizontal overflow`)
  evidence.checks.push({ key, nodes: snapshots[key].length, ...layout })
  if ([1440, 390].includes(width) && ['login', 'overview', 'form-errors', 'task-detail', 'notifications', 'reduced-transparency'].includes(state)) {
    await page.screenshot({ path: resolve(output, `${key}.png`), fullPage: true, animations: 'disabled' })
    evidence.screenshots.push(`${key}.png`)
  }
}
try {
  for (const width of [1440, 1180, 1000, 760, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', locale: 'zh-CN', timezoneId: 'Asia/Shanghai' })
    const page = await context.newPage()
    let mode = 0
    let releaseLoading
    page.on('pageerror', error => evidence.pageErrors.push(error.message))
    await page.route('**/api/v1/**', async route => {
      const request = route.request(), path = new URL(request.url()).pathname
      evidence.requests.push({ width, path, method: request.method(), fixture: true })
      assert.ok(request.method() === 'GET' || path.endsWith('/auth/login') || path.endsWith('/auth/logout'), 'unexpected business mutation')
      let data
      if (path.endsWith('/auth/login')) data = { access_token: 'synthetic-ui-token', user, expires_at: '2026-10-29T01:00:00Z', token_type: 'Bearer' }
      else if (path.endsWith('/auth/me')) data = user
      else if (path.endsWith('/auth/logout')) data = {}
      else if (path.endsWith('/dictionaries')) data = dictionaries
      else if (path.endsWith('/review-template')) data = template
      else if (path.endsWith('/escalation-rules')) data = { version: 1, scan_interval_seconds: 60, rules: [] }
      else if (path.endsWith('/projects')) data = pageData([project])
      else if (path.endsWith('/projects/1')) data = project
      else if (path.endsWith('/members')) data = pageData([member])
      else if (path.endsWith('/iterations')) data = pageData([iteration])
      else if (path.endsWith('/tasks/1')) data = task
      else if (path.endsWith('/tasks')) {
        if (mode === 'loading') await new Promise(done => { releaseLoading = done })
        if (typeof mode === 'number' && mode >= 400) return route.fulfill({ status: mode, json: { message: '合成错误用于界面核对', request_id: 'synthetic-ui-error' } })
        data = pageData(mode === 'empty' ? [] : [task])
      } else if (path.endsWith('/notifications')) data = { ...pageData([{ id: 1, project_id: 1, task_id: 1, title: '合成通知', message: '仅界面夹具', read_at: null, handled_at: null, fallback: true }]), unread_count: 1, unhandled_count: 1 }
      else throw new Error(`Unexpected fixture path: ${path}`)
      return route.fulfill({ status: 200, json: envelope(data) })
    })
    await page.goto(process.env.T44_STYLE_URL ?? 'http://127.0.0.1:5186/')
    await page.addStyleTag({ content: '*, *::before, *::after { animation: none !important; transition: none !important; }' })
    await capture(page, width, 'login')
    await page.locator('#login-username').fill('synthetic-ui-user')
    await page.locator('#login-password').fill('synthetic-ui-password')
    await page.locator('.login-submit').click()
    await page.locator('.business-card').first().waitFor()
    await capture(page, width, 'overview')
    await page.locator('.business-card .text-button').first().click()
    await page.locator('.task-toolbar').waitFor()
    await capture(page, width, 'task-detail')
    await page.keyboard.press('Escape')
    await page.locator('.task-toolbar').waitFor({ state: 'hidden' })
    await page.getByRole('button', { name: '登记交付任务', exact: true }).click()
    assert.equal(await page.locator('#field-title').inputValue(), '')
    assert.equal(await page.locator('#field-plan-buffer_hours').inputValue(), '')
    await capture(page, width, 'form-empty')
    await page.locator('.operation-form button[type="submit"]').click()
    await page.locator('.operation-form .field-error').first().waitFor()
    await capture(page, width, 'form-errors')
    await page.keyboard.press('Escape')
    await page.locator('.operation-form').waitFor({ state: 'hidden' })
    async function navigate(name) {
      if (width <= 760) await page.getByRole('button', { name: '打开主导航', exact: true }).click()
      const scope = width <= 760 ? page.locator('.mobile-navigation') : page.locator('.sidebar')
      await scope.getByRole('link', { name, exact: true }).click()
      await page.getByRole('heading', { name, exact: true, level: 1 }).waitFor()
      await page.locator('.data-state--loading').waitFor({ state: 'hidden' })
    }
    await navigate('通知中心')
    await page.getByRole('status', { name: '通知统计' }).waitFor()
    await capture(page, width, 'notifications')
    await navigate('交付任务')
    for (const status of [403, 409, 503, 'empty', 'loading']) {
      mode = status
      await page.getByRole('button', { name: '刷新记录', exact: true }).first().click()
      await page.locator(status === 'loading' ? '.data-state--loading' : '.data-state:not(.data-state--loading)').waitFor()
      await capture(page, width, `state-${status}`)
      if (status === 'loading') { mode = 0; releaseLoading(); await page.locator('.business-card').first().waitFor() }
    }
    const cdp = await context.newCDPSession(page)
    await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }, { name: 'prefers-reduced-transparency', value: 'reduce' }] })
    assert.ok(await page.evaluate(() => matchMedia('(prefers-reduced-transparency: reduce)').matches))
    await capture(page, width, 'reduced-transparency')
    await context.close()
  }
  assert.deepEqual(evidence.pageErrors, [])
  await writeFile(resolve(output, 'computed-styles.json.gz'), gzipSync(JSON.stringify(snapshots)))
  if (phase === 'after') {
    const before = JSON.parse(gunzipSync(await readFile(resolve(base, 'ui-before/computed-styles.json.gz'))))
    assert.deepEqual(Object.keys(snapshots), Object.keys(before))
    for (const key of Object.keys(snapshots)) {
      if (JSON.stringify(before[key]) !== JSON.stringify(snapshots[key])) {
        const changes = []
        for (let i = 0; i < Math.max(before[key].length, snapshots[key].length); i++) {
          if (JSON.stringify(before[key][i]) !== JSON.stringify(snapshots[key][i])) changes.push({ index: i, tag: snapshots[key][i]?.tag, class: snapshots[key][i]?.class })
        }
        evidence.differences.push({ key, changedNodes: changes.length, firstChanges: changes.slice(0, 12) })
      }
    }
    assert.deepEqual(evidence.differences, [], 'computed styles or layout changed')
  }
  evidence.passed = true
} catch (error) {
  evidence.passed = false
  evidence.failure = error.stack
  process.exitCode = 1
} finally {
  evidence.finishedAt = new Date().toISOString()
  await browser.close()
  await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(JSON.stringify({ phase, passed: evidence.passed, states: evidence.checks.length, screenshots: evidence.screenshots.length, differences: evidence.differences, failure: evidence.failure }))
}
