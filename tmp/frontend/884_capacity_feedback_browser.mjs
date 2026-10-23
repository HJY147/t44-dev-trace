import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { access, mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import { deepStrictEqual } from 'node:assert'

const origin = process.env.T44_UI_URL ?? 'http://127.0.0.1:5176'
const apiOrigin = 'http://127.0.0.1:18080'
if (origin !== 'http://127.0.0.1:5176') throw new Error('Developer browser is restricted to its own port5176')
const output = resolve(process.env.T44_UI_OUTPUT ?? 'agents/frontend/business-feedback-browser/first')
try { await access(resolve(output, 'results.json')); throw new Error('Refusing to overwrite results') } catch (error) { if (error.code !== 'ENOENT') throw error }
await mkdir(output, { recursive: true })
const credential = JSON.parse(await readFile(process.env.T44_UI_CREDENTIALS, 'utf8'))
if (credential.developer.user_id !== 2 || credential.reviewer.user_id !== 3) throw new Error('Expected explicitly authorized synthetic user2/user3')
const contract = JSON.parse(await readFile('specs/contracts/openapi.json', 'utf8'))
const operations = Object.fromEntries(Object.entries(contract.paths).flatMap(([path, item]) => Object.entries(item).filter(([, op]) => op.operationId).map(([method, op]) => [op.operationId, { path, method: method.toUpperCase() }])))
const evidence = { operator: 'AI frontend developer', startedAt: new Date().toISOString(), origin, apiOrigin, fixtureRequests: [], browserResponses: [], resources: {}, checks: [], screenshots: [], layouts: [], pageErrors: [], successfulBrowserBusinessWrites: 0, cleanup: 'New synthetic project and related records retained to preserve audit history; no deletion or seed/reset; no existing project/global-account modifications.' }
let token = '', browser
async function call(operation, params = {}, body) {
  const op = operations[operation], path = '/api/v1' + op.path.replace(/\{(\w+)\}/g, (_, key) => encodeURIComponent(String(params[key])))
  const headers = { Accept: 'application/json' }
  if (token) headers.Authorization = 'Bearer ' + token
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (operation !== 'login' && !['GET', 'HEAD'].includes(op.method)) headers['Idempotency-Key'] = randomUUID()
  const response = await fetch(apiOrigin + path, { method: op.method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  const payload = await response.json()
  evidence.fixtureRequests.push({ operation, method: op.method, path, status: response.status, code: payload.code ?? null, requestId: payload.meta?.request_id ?? payload.request_id ?? null })
  if (!response.ok) throw new Error('Synthetic setup/read rejected: ' + operation + ' HTTP' + response.status + ' ' + String(payload.code))
  return payload.data
}
const iterationState = data => ({ id: data.id, version: data.version, plan_version: data.plan_version, capacity: data.plan.capacity })
const taskState = data => ({ id: data.id, owner_id: data.owner_id, state: data.state, version: data.version, schedule_version: data.schedule_version })
async function capture(page, name) {
  await page.evaluate(async () => { await document.fonts.ready; await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))); await Promise.all(document.getAnimations().filter(animation => animation.effect?.getComputedTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => {}))) })
  const file = name + '.png'; await page.screenshot({ path: resolve(output, file), animations: 'disabled' }); evidence.screenshots.push(file)
  evidence.layouts.push(await page.evaluate(label => ({ label, width: innerWidth, scrollWidth: document.documentElement.scrollWidth }), name))
}
async function proof(page) {
  await page.locator('#field-reason').fill('Synthetic UI002 rejection evidence; retain original staffing')
  await page.locator('#field-evidence-0-kind').selectOption('3')
  await page.locator('#field-evidence-0-locator').fill('https://example.com/t44/frontend-ui002')
  await page.locator('#field-evidence-0-description').fill('Synthetic developer verification only')
}
async function reject(page, path, required) {
  const pending = page.waitForResponse(response => new URL(response.url()).pathname === path && response.request().method() === 'PATCH')
  await page.locator('.operation-form button[type="submit"]').click(); const response = await pending, body = await response.json()
  if (response.status() !== 422 || body.code !== 'CAPACITY_REFERENCE_INVALID') throw new Error('Expected real capacity422, received HTTP' + response.status() + ' ' + String(body.code))
  const alert = page.locator('.operation-error'); await alert.waitFor(); const text = await alert.textContent()
  for (const phrase of required) if (!text.includes(phrase)) throw new Error('Missing business explanation: ' + phrase)
  if (text.includes('请修改提示的字段')) throw new Error('Business guard still shown as ordinary field validation')
  await alert.scrollIntoViewIfNeeded()
  return { status: response.status(), code: body.code, requestId: body.request_id, alertText: text }
}
try {
  const login = await call('login', {}, { username: credential.manager.username, password: credential.manager.password }); token = login.access_token
  const suffix = new Date().toISOString().replace(/\D/g, '') + '-' + randomUUID().slice(0, 6)
  let project, iteration, task
  if (process.env.T44_UI_RESUME_RESULT) {
    const previous = JSON.parse(await readFile(process.env.T44_UI_RESUME_RESULT, 'utf8'))
    if (!previous.resources.project?.name?.startsWith('[synthetic][frontend UI002] ')) throw new Error('Can resume only this developer project checkpoint')
    project = await call('getProject', { project_id: previous.resources.project.id })
    if (project.name !== previous.resources.project.name || project.created_by !== credential.manager.user_id) throw new Error('Owned project checkpoint identity mismatch')
    const params = { project_id: project.id }
    const members = await call('listProjectMembers', params), iterations = await call('listIterations', params), tasks = await call('listTasks', params)
    if (previous.resources.iteration) {
      if (JSON.stringify(members.items.map(item => item.user.id).sort()) !== '[1,2,3]' || iterations.total !== 1 || tasks.total !== 1) throw new Error('Initialized own fixture membership/resource counts changed')
      iteration = iterations.items[0]; deepStrictEqual(iterationState(iteration), previous.resources.iteration)
      task = await call('getTask', { ...params, task_id: tasks.items[0].id })
      if (task.iteration_id !== iteration.id || task.owner_id !== 2 || task.version !== 1 || task.state !== 1 || task.title !== 'Synthetic UI002 active owner') throw new Error('Initialized own task identity changed')
      evidence.resumedOwnInitializedProject = true
    } else {
      if (members.items.length !== 1 || members.items[0].user.id !== credential.manager.user_id || iterations.total || tasks.total) throw new Error('Owned project checkpoint is no longer empty')
      evidence.resumedOwnEmptyProject = true
    }
  } else project = await call('createProject', {}, { name: '[synthetic][frontend UI002] ' + suffix, description: 'Owned developer-only rejection fixture; not an independent test or real project.' })
  evidence.resources.project = { id: project.id, name: project.name }
  const params = { project_id: project.id }
  if (!iteration) {
    for (const account of [credential.developer, credential.reviewer]) await call('addProjectMember', params, { username: account.username, roles: [2], reason: 'Synthetic frontend UI002 own-project fixture only' })
    const start = Date.now() + 2 * 86400000, time = offset => new Date(start + offset).toISOString()
    iteration = await call('createIteration', params, { name: 'Synthetic UI002 staffing', planned_start: time(0), planned_end: time(3 * 86400000), capacity: [{ user_id: 2, available_hours: 8 }], buffer_hours: 1, delay_contingency: 'Retain active owner staffing until legitimate lifecycle completion' })
    evidence.resources.iteration = iterationState(iteration)
    task = (await call('createTask', params, { title: 'Synthetic UI002 active owner', description: 'Own fixture; expected rejected writes must preserve owner/version', iteration_id: iteration.id, owner_id: 2, dependency_task_ids: [], plan: { planned_start: time(3600000), planned_end: time(8 * 3600000), estimated_hours: 2, buffer_hours: 0.5, delay_contingency: 'Manager retains staffing and records any later legitimate decision' } })).task
  }
  if (!task?.id) throw new Error('No concrete owned task after TaskMutation decoding')
  evidence.resources.iteration = iterationState(iteration); evidence.resources.task = taskState(task)
  browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', locale: 'zh-CN', timezoneId: 'Asia/Shanghai' })
    const page = await context.newPage(); page.on('pageerror', error => evidence.pageErrors.push(error.message))
    page.on('response', response => { const path = new URL(response.url()).pathname; if (!path.startsWith('/api/v1/')) return; const method = response.request().method(); evidence.browserResponses.push({ width, method, path, status: response.status(), requestId: response.headers()['x-request-id'] ?? null }); if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && !['/api/v1/auth/login', '/api/v1/auth/logout'].includes(path) && response.status() < 400) evidence.successfulBrowserBusinessWrites++ })
    await page.goto(origin + '/schedule'); await page.locator('#login-username').fill(credential.manager.username); await page.locator('#login-password').fill(credential.manager.password); await page.locator('.login-submit').click(); await page.locator('.login-page').waitFor({ state: 'hidden' })
    await page.locator('.project-picker select').selectOption(String(project.id))
    const card = page.locator('.business-card').filter({ has: page.getByRole('heading', { name: iteration.plan.name, exact: true }) }); await card.waitFor()
    await card.getByRole('button', { name: '调整迭代与容量', exact: true }).click()
    await page.locator('#field-plan-capacity-0-user_id').selectOption('3'); await proof(page)
    const capacity = await reject(page, `/api/v1/projects/${project.id}/iterations/${iteration.id}`, ['未结项任务', '保留', '已回滚', '不重复'])
    const capacityAfter = iterationState((await call('listIterations', params)).items.find(item => item.id === iteration.id)); deepStrictEqual(capacityAfter, evidence.resources.iteration)
    await capture(page, `${width}-capacity-rejection`); await page.getByRole('button', { name: '取消', exact: true }).click(); await page.locator('.operation-form').waitFor({ state: 'hidden' })
    if (width === 390) await page.getByRole('button', { name: '打开主导航', exact: true }).click()
    await page.getByRole('link', { name: '交付任务', exact: true }).click(); if (width === 390) await page.getByRole('button', { name: '关闭主导航', exact: true }).waitFor({ state: 'hidden' })
    await page.getByRole('button', { name: task.title, exact: true }).click(); await page.getByRole('button', { name: '调整负责人', exact: true }).click()
    await page.locator('#field-owner_id').selectOption('3'); await proof(page)
    const assignment = await reject(page, `/api/v1/projects/${project.id}/tasks/${task.id}/assignment`, ['接手人', '当前迭代', '先', '工时'])
    const taskAfter = taskState(await call('getTask', { ...params, task_id: task.id })); deepStrictEqual(taskAfter, evidence.resources.task)
    await capture(page, `${width}-assignment-rejection`); await page.getByRole('button', { name: '取消', exact: true }).click(); await page.locator('.operation-form').waitFor({ state: 'hidden' }); await page.keyboard.press('Escape'); await page.locator('.task-toolbar').waitFor({ state: 'hidden' })
    evidence.checks.push({ width, capacity, capacityAfter, assignment, taskAfter, dataAndVersionsUnchanged: true })
    await page.getByRole('button', { name: '退出', exact: true }).click(); await page.locator('.login-page').waitFor(); await context.close()
  }
  await call('logout'); token = ''
  evidence.passed = !evidence.pageErrors.length && !evidence.successfulBrowserBusinessWrites && evidence.layouts.every(item => item.scrollWidth <= item.width)
  if (!evidence.passed) process.exitCode = 1
} catch (error) { evidence.passed = false; evidence.failure = error.message; process.exitCode = 1 }
finally { if (browser) await browser.close(); evidence.finishedAt = new Date().toISOString(); evidence.chromeClosed = true; await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n'); console.log(JSON.stringify(evidence)) }
