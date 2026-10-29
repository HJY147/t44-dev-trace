import assert from 'node:assert/strict'
import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright')
const credentials = JSON.parse(await readFile(process.env.DEMO_CREDENTIALS, 'utf8'))
const phase = process.env.PHASE || 'before'
const output = process.env.FRONTEND_BROWSER_OUTPUT || fileURLToPath(new URL('../../agents/frontend/integration-browser/', import.meta.url))
await mkdir(output, { recursive: true })
const candidateSource = JSON.parse(await readFile(process.env.CSS_CANDIDATES || new URL('../../agents/frontend/integration-css-removal.json', import.meta.url), 'utf8'))
const candidates = candidateSource.candidates || candidateSource.removed
const redact = (message) => Object.values(credentials).filter(v => v?.password).reduce((s, r) => s.replaceAll(r.password, '[REDACTED]'), message)
if (phase === 'escalate') {
  const service = JSON.parse(await readFile(process.env.SERVICE_CREDENTIALS, 'utf8'))
  const task = JSON.parse(await readFile(process.env.PREPARED_TASK || new URL('../../agents/frontend/integration-browser/prepared-task.json', import.meta.url), 'utf8'))
  const body = { expected_version: task.expected_version, schedule_version: task.schedule_version, rule_version: 1, scan_run_id: crypto.randomUUID() }
  const response = await fetch(`http://127.0.0.1:18080/api/v1/internal/projects/${task.project_id}/tasks/${task.task_id}/escalations`, { method: 'POST', headers: { Authorization: `Bearer ${service.access_token}`, 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify(body) })
  const payload = await response.json()
  const result = { status: response.status, project_id: task.project_id, task_id: task.task_id, data: payload.data ?? null, code: payload.code ?? null, request_id: payload.meta?.request_id ?? payload.request_id }
  await writeFile(join(output, 'escalation-preparation.json'), JSON.stringify(result, null, 2) + '\n')
  console.log(JSON.stringify(result)); process.exit(response.ok ? 0 : 1)
}
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN', reducedMotion: 'reduce' })
const errors = [], consoleErrors = [], http = [], checks = [], captures = [], matches = []
page.on('pageerror', e => errors.push(redact(e.message)))
page.on('console', m => { if (m.type() === 'error') consoleErrors.push(redact(m.text())) })
page.on('response', r => { const u = new URL(r.url()); if (u.pathname.startsWith('/api/v1')) http.push({ method: r.request().method(), path: u.pathname, status: r.status(), request_id: r.headers()['x-request-id'] || null }) })
const projectId = credentials._integration.project_id, taskId = Number(process.env.NOTIFICATION_TASK_ID || credentials._integration.task_id)
const button = name => page.getByRole('button', { name, exact: true })
async function nav(name) {
  if (await page.locator('.sidebar').isVisible()) await page.locator('.sidebar').getByRole('link', { name, exact: true }).click()
  else { await button('打开主导航').click(); await page.getByRole('dialog', { name: '主导航' }).getByRole('link', { name, exact: true }).click() }
  await page.waitForLoadState('networkidle')
  await page.locator('.data-state--loading').waitFor({ state: 'hidden' })
}
async function evidence() {
  await page.locator('#field-evidence-0-kind').selectOption('2')
  await page.locator('#field-evidence-0-locator').fill('tmp/frontend/958_integration-browser.mjs')
  await page.locator('#field-evidence-0-description').fill('隔离演示项目真实前端回归：迭代嵌套计划与容量')
}
async function submit(name, path, method) {
  const pending = page.waitForResponse(r => new URL(r.url()).pathname === path && r.request().method() === method)
  await button(name).click()
  const response = await pending
  assert.equal(response.ok(), true, `${method} ${path}: ${response.status()}`)
  const result = await response.json()
  await page.locator('.operation-form').waitFor({ state: 'hidden' })
  await page.waitForLoadState('networkidle')
  return result.data
}
try {
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' })
  await page.locator('#login-username').fill(credentials.manager.username)
  await page.locator('#login-password').fill(credentials.manager.password)
  await button('登录').click(); await page.locator('.login-page').waitFor({ state: 'hidden' })
  await page.locator('.project-picker select').selectOption(String(projectId))
  await page.waitForLoadState('networkidle')
  checks.push('真实经理账号登录，选择升级链演示项目')
  if (phase === 'counts') {
    assert.ok(process.env.BACKEND_SHA, '真实后端ready SHA必须提供')
    const snapshots = []
    async function totals(data, step, requestId = null) {
      const text = await page.getByRole('status', { name: '通知统计' }).innerText()
      assert.ok(text.includes(`未读 ${data.unread_count} 条`)); assert.ok(text.includes(`未处理 ${data.unhandled_count} 条`))
      snapshots.push({ step, request_id: requestId, project_id: Number(await page.locator('.project-picker select').inputValue()), unread_count: data.unread_count, unhandled_count: data.unhandled_count, total: data.total, visible_rows: data.items.length })
    }
    async function fresh(step) {
      const pending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me/notifications')
      await page.locator('.page-heading').getByRole('button', { name: '刷新记录', exact: true }).click()
      const response = await pending; assert.equal(response.status(), 200)
      const envelope = await response.json(), data = envelope.data
      await page.waitForLoadState('networkidle'); await totals(data, step, envelope.meta?.request_id); return data
    }
    const notificationCard = id => page.locator('.business-card').filter({ has: page.getByText(`编号 ${id}`, { exact: true }) })
    async function taskSnapshot(card) {
      const pending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/tasks/${taskId}`)
      await card.getByRole('button', { name: '查看相关任务', exact: true }).click()
      const task = (await (await pending).json()).data
      await page.locator('.el-drawer__close-btn:visible').click()
      await page.getByRole('dialog', { name: task.title, exact: true }).waitFor({ state: 'hidden' })
      return task
    }
    await nav('通知中心'); const initial = await fresh('initial')
    const notification = initial.items.find(n => n.task_id === taskId && !n.read_at && !n.handled_at)
    assert.ok(notification, '只使用新建且未读未处理的真实通知，不重置旧项')
    const before = await taskSnapshot(notificationCard(notification.id))
    await page.screenshot({ path: join(output, 'counts-desktop-initial.png'), fullPage: true }); captures.push('counts-desktop-initial.png')
    await notificationCard(notification.id).getByRole('button', { name: '记录处理结果', exact: true }).click()
    await page.locator('#field-note').fill('双计数真实回归：先处理仍未读，阅读独立操作；不改变任务状态')
    await evidence()
    const handled = await submit('确认记录通知处理结果', `/api/v1/projects/${projectId}/notifications/${notification.id}/handling`, 'POST')
    assert.equal(handled.read_at, null); assert.ok(handled.handled_at)
    const afterHandle = await fresh('handled-but-unread')
    assert.equal(afterHandle.unread_count, initial.unread_count); assert.equal(afterHandle.unhandled_count, initial.unhandled_count - 1)
    const middleTask = await taskSnapshot(notificationCard(notification.id))
    assert.equal(middleTask.version, before.version); assert.equal(middleTask.state, before.state)
    await page.setViewportSize({ width: 390, height: 844 }); await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
    await page.screenshot({ path: join(output, 'counts-mobile-handled-unread.png'), fullPage: true }); captures.push('counts-mobile-handled-unread.png')
    await notificationCard(notification.id).getByRole('button', { name: '标记已读', exact: true }).click()
    const read = await submit('确认标记通知已读', `/api/v1/projects/${projectId}/notifications/${notification.id}/read`, 'POST')
    assert.ok(read.read_at); assert.ok(read.handled_at)
    const afterRead = await fresh('read-and-handled')
    assert.equal(afterRead.unread_count, afterHandle.unread_count - 1); assert.equal(afterRead.unhandled_count, afterHandle.unhandled_count)
    const after = await taskSnapshot(notificationCard(notification.id))
    assert.equal(after.version, before.version); assert.equal(after.state, before.state)
    await page.setViewportSize({ width: 1440, height: 1000 })
    const alternateId = String(credentials._demo.project_id)
    const switchedPending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me/notifications' && new URL(r.url()).searchParams.get('project_id') === alternateId)
    await page.locator('.project-picker select').selectOption(alternateId)
    const switchedEnvelope = await (await switchedPending).json(), switched = switchedEnvelope.data
    await page.waitForLoadState('networkidle'); await totals(switched, 'alternate-project', switchedEnvelope.meta?.request_id)
    const restoredPending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me/notifications' && new URL(r.url()).searchParams.get('project_id') === String(projectId))
    await page.locator('.project-picker select').selectOption(String(projectId))
    const restoredEnvelope = await (await restoredPending).json(), restored = restoredEnvelope.data
    await page.waitForLoadState('networkidle'); await totals(restored, 'restored-project', restoredEnvelope.meta?.request_id)
    await page.route('**/api/v1/me/notifications*', route => route.abort('failed'), { times: 1 })
    await page.locator('.page-heading').getByRole('button', { name: '刷新记录', exact: true }).click(); await page.getByText('暂时无法加载', { exact: true }).waitFor()
    assert.equal(await page.getByRole('status', { name: '通知统计' }).count(), 0)
    await page.screenshot({ path: join(output, 'counts-network-error-hidden.png'), fullPage: true }); captures.push('counts-network-error-hidden.png')
    await page.unroute('**/api/v1/me/notifications*')
    await fresh('recovered-real-api')
    assert.equal(errors.length, 0)
    assert.ok(consoleErrors.every(message => message.includes('ERR_FAILED')))
    const result = { frontend_sha: 'f6547f237bba12262b95d2701a7d0c9c0b474280', backend_sha: process.env.BACKEND_SHA, source: 'real browser/Vite same-origin → root-ready dev API18080 → t44_dev; no fake response/status', scope: '前端开发回归，非独立复测；network error由一次真实请求abort控制注入', project_id: projectId, notification_id: notification.id, task_id: taskId, task_versions: [before.version, middleTask.version, after.version], task_states: [before.state, middleTask.state, after.state], snapshots, http, browserErrors: errors, consoleErrors, screenshots: captures }
    await writeFile(join(output, 'counts-result.json'), JSON.stringify(result, null, 2) + '\n')
    console.log(JSON.stringify({ backend_sha: process.env.BACKEND_SHA, project_id: projectId, notification_id: notification.id, task_id: taskId, task_versions: result.task_versions, task_states: result.task_states, snapshots, httpCount: http.length, browserErrors: errors.length, controlledNetworkConsoleErrors: consoleErrors.length }))
    await browser.close(); process.exit(0)
  }
  if (['prepare', 'counts-prepare'].includes(phase)) {
    await nav('迭代排期')
    const pending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/iterations`)
    await button('刷新记录').click()
    const iterations = (await (await pending).json()).data.items
    const iteration = iterations.find(i => i.id === credentials._integration.iteration_id)
    assert.ok(iteration)
    await nav('交付任务'); await button('登记交付任务').click()
    await page.locator('#field-title').fill((phase === 'counts-prepare' ? '前端通知双计数回归 ' : '前端通知读与处理回归 ') + Date.now())
    await page.locator('#field-description').fill('隔离演示任务，由本岗真实页面创建；升级后验证读与处理分开，不更改旧事件')
    await page.locator('#field-iteration_id').selectOption(String(iteration.id))
    await page.locator('#field-owner_id').selectOption(String(credentials.developer.user_id))
    const local = iso => new Date(new Date(iso).getTime() + 8 * 3600000).toISOString().slice(0, 16)
    await page.locator('#field-plan-planned_start').fill(local(iteration.plan.planned_start))
    await page.locator('#field-plan-planned_end').fill(local(iteration.plan.planned_end))
    await page.locator('#field-plan-estimated_hours').fill('1'); await page.locator('#field-plan-buffer_hours').fill('0')
    await page.locator('#field-plan-delay_contingency').fill('由总协调仅针对本条新任务触发真实升级，保留原通知历史')
    const created = await submit('确认登记交付任务', `/api/v1/projects/${projectId}/tasks`, 'POST')
    const task = created.task
    const prepared = { project_id: projectId, task_id: task.id, expected_version: task.version, schedule_version: task.schedule_version, iteration_id: iteration.id, planned_end: task.plan.planned_end }
    await writeFile(join(output, 'prepared-task.json'), JSON.stringify(prepared, null, 2) + '\n')
    console.log(JSON.stringify(prepared)); await browser.close(); process.exit(0)
  }
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 })
    for (const [label, key] of [['工作台', 'overview'], ['交付任务', 'tasks'], ['迭代排期', 'schedule'], ['通知中心', 'notifications'], ['审计记录', 'audit'], ['项目空间', 'projects'], ['评审与发布', 'reviews']]) {
      await nav(label)
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${width} ${label}: horizontal overflow`)
      matches.push({ width, page: key, checked_selectors: candidates.length, counts: await page.evaluate(selectors => selectors.map(s => ({ selector: s, count: document.querySelectorAll(s.replaceAll(/::[\w-]+/g, '')).length })), candidates.map(c => c.selector)).then(counts => counts.filter(item => item.count > 0)) })
      if (['tasks', 'schedule', 'notifications'].includes(key)) {
        const file = `${phase}-${width}-${key}.png`
        await page.screenshot({ path: join(output, file), fullPage: true }); captures.push(file)
      }
      if (key === 'notifications') {
        await page.getByRole('tab', { name: '升级规则', exact: true }).click()
        await page.getByText('扫描间隔（秒）', { exact: true }).waitFor()
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
        matches.push({ width, page: 'rules', checked_selectors: candidates.length, counts: await page.evaluate(selectors => selectors.map(s => ({ selector: s, count: document.querySelectorAll(s.replaceAll(/::[\w-]+/g, '')).length })), candidates.map(c => c.selector)).then(counts => counts.filter(item => item.count > 0)) })
      }
    }
  }
  checks.push('1440/390七个页面与规则：候选样式DOM核对、手机导航和整页无横向溢出')
  await writeFile(join(output, `${phase}-layout-result.json`), JSON.stringify({ phase, http, browserErrors: errors, consoleErrors, candidatesMatched: matches, screenshots: captures }, null, 2) + '\n')
  if (['after', 'final'].includes(phase)) {
    await page.setViewportSize({ width: 1440, height: 1000 })
    await nav('迭代排期'); await button('新建迭代与容量').click()
    const name = '前端嵌套计划回归 ' + Date.now()
    for (const [id, value] of Object.entries({ name, planned_start: '2026-10-23T09:00', planned_end: '2026-10-30T18:00', buffer_hours: '2', delay_contingency: '演示容量变更需逐项留痕' })) await page.locator('#field-' + id).fill(value)
    await page.locator('#field-capacity-0-user_id').selectOption(String(credentials.developer.user_id))
    await page.locator('#field-capacity-0-available_hours').fill('8')
    const iteration = await submit('确认新建迭代', `/api/v1/projects/${projectId}/iterations`, 'POST')
    assert.equal(iteration.plan.name, name)
    const card = page.locator('.business-card').filter({ has: page.getByRole('heading', { name, exact: true }) })
    await card.getByRole('button', { name: '调整迭代与容量', exact: true }).click()
    assert.equal(await page.locator('#field-plan-name').inputValue(), name)
    assert.equal(await page.locator('#field-plan-capacity-0-available_hours').inputValue(), '8')
    assert.equal(await page.locator('#field-expected_version').inputValue(), String(iteration.version))
    await page.locator('#field-plan-capacity-0-available_hours').fill('12'); await page.locator('#field-reason').fill('正式缺陷C-P1真实HTTP回归，容量8改12')
    await evidence()
    const changed = await submit('确认调整迭代与容量', `/api/v1/projects/${projectId}/iterations/${iteration.id}`, 'PATCH')
    assert.equal(changed.plan.name, name); assert.equal(changed.plan.capacity[0].available_hours, 12)
    checks.push('C-P1真实UI创建迭代→完整嵌套预填→容量调整→HTTP响应保留计划与新容量')
    await nav('交付任务'); await button('登记交付任务').click()
    assert.equal(await page.locator(`#field-iteration_id option[value="${iteration.id}"]`).textContent(), name)
    await button('取消').click(); checks.push('真实迭代下拉名称显示')
    await nav('通知中心')
    const listPending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me/notifications' && r.request().method() === 'GET')
    await button('刷新记录').click()
    const list = (await (await listPending).json()).data
    const notification = list.items.find(n => n.task_id === taskId && !n.read_at && !n.handled_at)
    if (!notification) checks.push({ visibleNotifications: list.items.map(n => ({ id: n.id, task_id: n.task_id, project_id: n.project_id, read_at: n.read_at, handled_at: n.handled_at })) }); assert.ok(notification, '经理保留的真实未读、未处理通知存在')
    let cardNotification = page.locator('.business-card').filter({ hasText: `编号 ${notification.id}` }).filter({ hasText: notification.title })
    const taskPending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/tasks/${taskId}`)
    await cardNotification.getByRole('button', { name: '查看相关任务', exact: true }).click()
    const before = (await (await taskPending).json()).data
    await page.locator('.el-drawer__close-btn:visible').click()
    await cardNotification.getByRole('button', { name: '标记已读', exact: true }).click()
    assert.equal(await page.locator('#field-note').count(), 0)
    const read = await submit('确认标记通知已读', `/api/v1/projects/${projectId}/notifications/${notification.id}/read`, 'POST')
    assert.ok(read.read_at); assert.equal(read.handled_at, null)
    cardNotification = page.locator('.business-card').filter({ hasText: `编号 ${notification.id}` }).filter({ hasText: notification.title })
    assert.equal(await cardNotification.getByRole('button', { name: '标记已读', exact: true }).isDisabled(), true)
    assert.equal(await cardNotification.getByRole('button', { name: '记录处理结果', exact: true }).isEnabled(), true)
    const readTaskPending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/tasks/${taskId}`)
    await cardNotification.getByRole('button', { name: '查看相关任务', exact: true }).click()
    const afterRead = (await (await readTaskPending).json()).data
    assert.equal(afterRead.version, before.version); assert.equal(afterRead.state, before.state)
    await page.locator('.el-drawer__close-btn:visible').click()
    await page.screenshot({ path: join(output, `${phase}-after-read.png`), fullPage: true }); captures.push(`${phase}-after-read.png`)
    await cardNotification.getByRole('button', { name: '记录处理结果', exact: true }).click()
    await page.locator('#field-note').fill('前端真实通知回归：已核实降级提醒，阅读与处理分开；不解除任务阻塞')
    await evidence()
    const handled = await submit('确认记录通知处理结果', `/api/v1/projects/${projectId}/notifications/${notification.id}/handling`, 'POST')
    assert.ok(handled.read_at); assert.ok(handled.handled_at)
    cardNotification = page.locator('.business-card').filter({ hasText: `编号 ${notification.id}` }).filter({ hasText: notification.title })
    assert.equal(await cardNotification.getByRole('button', { name: '记录处理结果', exact: true }).isDisabled(), true)
    const handledTaskPending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/tasks/${taskId}`)
    await cardNotification.getByRole('button', { name: '查看相关任务', exact: true }).click()
    const afterHandle = (await (await handledTaskPending).json()).data
    assert.equal(afterHandle.version, before.version); assert.equal(afterHandle.state, before.state)
    await page.locator('.el-drawer__close-btn:visible').click()
    checks.push({ notification_id: notification.id, task_id: taskId, task_version: before.version, task_state: before.state, result: '真实已读后仍未处理；显式处理后完成；三次权威GET任务版本/状态均不变' })
    await page.getByRole('dialog', { name: afterHandle.title, exact: true }).waitFor({ state: 'hidden' })
    await page.setViewportSize({ width: 390, height: 844 }); assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
    await page.screenshot({ path: join(output, `${phase}-after-handled-mobile.png`), fullPage: true }); captures.push(`${phase}-after-handled-mobile.png`)
    await page.setViewportSize({ width: 1440, height: 1000 })
    await page.getByRole('tab', { name: '项目升级历史', exact: true }).click()
    await page.locator('.business-card').first().waitFor(); await page.locator('.business-card details > summary').first().click(); assert.ok((await page.locator('.business-panel').innerText()).includes('收件人'))
    await page.getByRole('tab', { name: '升级规则', exact: true }).click(); await page.getByText('扫描间隔（秒）', { exact: true }).waitFor()
    await nav('审计记录'); await page.locator('.business-card').first().waitFor()
    checks.push('真实升级列表、规则与包含迭代改期/通知操作的项目审计可见')
  }
  if (phase === 'resume') {
    await page.setViewportSize({ width: 1440, height: 1000 }); await nav('通知中心')
    const pending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me/notifications')
    await button('刷新记录').click()
    const list = (await (await pending).json()).data
    const notification = list.items.find(n => n.task_id === taskId)
    assert.ok(notification.read_at); assert.ok(notification.handled_at)
    const card = page.locator('.business-card').filter({ hasText: `编号 ${notification.id}` }).filter({ hasText: notification.title })
    assert.equal(await card.getByRole('button', { name: '标记已读', exact: true }).isDisabled(), true)
    assert.equal(await card.getByRole('button', { name: '记录处理结果', exact: true }).isDisabled(), true)
    const taskPending = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/projects/${projectId}/tasks/${taskId}`)
    await card.getByRole('button', { name: '查看相关任务', exact: true }).click()
    const task = (await (await taskPending).json()).data
    assert.equal(task.version, 2); assert.equal(task.state, 1)
    await page.locator('.el-drawer__close-btn:visible').click()
    await page.setViewportSize({ width: 390, height: 844 })
    const immediateOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
    await page.getByRole('dialog', { name: task.title, exact: true }).waitFor({ state: 'hidden' })
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
    await page.waitForLoadState('networkidle')
    const settledOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
    assert.equal(settledOverflow, false)
    await page.screenshot({ path: join(output, 'resume-handled-mobile.png'), fullPage: true }); captures.push('resume-handled-mobile.png')
    checks.push({ notification_id: notification.id, task_id: taskId, task_version: task.version, task_state: task.state, immediateOverflow, settledOverflow, result: '只读复查真实已处理状态/按钮、关闭抽屉后稳定手机布局；不重放通知写' })
    await nav('通知中心'); await page.getByRole('tab', { name: '项目升级历史', exact: true }).click()
    await page.locator('.business-card').first().waitFor(); await page.locator('.business-card details > summary').first().click(); assert.ok((await page.locator('.business-panel').innerText()).includes('收件人'))
    await page.getByRole('tab', { name: '升级规则', exact: true }).click(); await page.getByText('扫描间隔（秒）', { exact: true }).waitFor()
    await nav('审计记录'); await page.locator('.business-card').first().waitFor()
    checks.push('真实升级列表、规则与通知/迭代审计只读复查')
  }
  assert.equal(errors.length, 0); assert.equal(consoleErrors.length, 0)
  assert.equal(http.some(r => r.status >= 400), false)
  await writeFile(join(output, `${phase}-result.json`), JSON.stringify({ phase, transport: 'browser → Vite5173 proxy → real FastAPI18080 → MySQL; no fetch substitution', scope: '前端模块真实联调，非独立验收、非Rabbit成功链或性能结论', checks, http, browserErrors: errors, consoleErrors, candidatesMatched: matches, screenshots: captures }, null, 2) + '\n')
  console.log(JSON.stringify({ phase, checks, httpCount: http.length, browserErrors: errors.length, consoleErrors: consoleErrors.length }))
} catch (error) {
  await page.screenshot({ path: join(output, `${phase}-failure.png`), fullPage: true }).catch(() => {})
  await writeFile(join(output, `${phase}-failure-${Date.now()}.json`), JSON.stringify({ phase, checks, http, browserErrors: errors, consoleErrors, error: redact(error.message), stack: redact(error.stack || ''), overflowingElements: await page.evaluate(() => [...document.querySelectorAll('body *')].map(e => ({ tag: e.tagName, class: e.className?.baseVal ?? e.className, left: e.getBoundingClientRect().left, right: e.getBoundingClientRect().right })).filter(e => e.right > innerWidth + 1 || e.left < -1).slice(0, 20)), formErrors: await page.locator('.field-error').allTextContents(), candidatesMatched: matches, screenshots: captures }, null, 2) + '\n')
  console.error(redact(error.message)); process.exitCode = 1
} finally { await browser.close() }
