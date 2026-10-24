import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { access, mkdir, readFile, realpath, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { randomUUID, createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { deepStrictEqual } from 'node:assert'
import { createServer } from '../../frontend/node_modules/vite/dist/node/index.js'

const apiBase = 'http://127.0.0.1:18089', legacyBase = 'http://127.0.0.1:18080', origin = 'http://127.0.0.1:5176'
const frontendSource = 'c79cd9930febadfa77cb2d0eede7626d4039c305', backendSource = '0549ea89ce218ecb945cd4346671f20d46fad215'
if (process.env.T44_REASON_BACKEND_SOURCE !== backendSource) throw new Error('Exact coordinator backend source is required')
const output = resolve(process.env.T44_UI_OUTPUT ?? 'agents/frontend/plan-reason-browser/first')
try { await access(resolve(output, 'results.json')); throw new Error('Refusing to overwrite results') } catch (error) { if (error.code !== 'ENOENT') throw error }
await mkdir(output, { recursive: true })
const credential = JSON.parse(await readFile(process.env.T44_UI_CREDENTIALS, 'utf8'))
const contract = JSON.parse(await readFile('specs/contracts/openapi.json', 'utf8'))
const require = createRequire(import.meta.url), AjvModule = require('../../frontend/node_modules/ajv/dist/2020.js'), FormatModule = require('../../frontend/node_modules/ajv-formats')
const ajv = new (AjvModule.default ?? AjvModule)({ strict: false, allErrors: true }); (FormatModule.default ?? FormatModule)(ajv)
const operations = Object.fromEntries(Object.entries(contract.paths).flatMap(([path, item]) => Object.entries(item).filter(([, op]) => op.operationId).map(([method, op]) => [op.operationId, { ...op, path, method: method.toUpperCase() }])))
const sha = value => createHash('sha256').update(value).digest('hex')
const evidence = { operator: 'AI frontend developer', startedAt: new Date().toISOString(), frontendSource, backendSource, legacyBackendSource: '5dcb73cc10c38deb14fae68d33318b04d538fecf', apiBase, legacyBase, origin, coordinatorBackendPid: 12156, sourceChecks: {}, controlRequests: [], browserResponses: [], resources: {}, checks: [], screenshots: [], pageErrors: [], layouts: [], cleanup: 'Only a new owned synthetic project/member/iteration/task; retained for audit, no deletion/reset, no old project41/independent data modifications.' }
let token = '', browser, server
function checkSchema(schema, value, label) {
  const valid = ajv.compile({ components: contract.components, ...schema })
  if (!valid(value)) throw new Error(label + ' schema rejected: ' + JSON.stringify(valid.errors?.map(error => ({ path: error.instancePath, message: error.message }))))
}
async function call(operation, params = {}, body, base = apiBase, query = {}) {
  const op = operations[operation]
  if (!op) throw new Error('Unknown frozen operation ' + operation)
  if (body !== undefined) checkSchema(op.requestBody.content['application/json'].schema, body, operation + ' request')
  const path = '/api/v1' + op.path.replace(/\{(\w+)\}/g, (_, key) => encodeURIComponent(String(params[key])))
  const headers = { Accept: 'application/json' }; if (token) headers.Authorization = 'Bearer ' + token
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (!['login', 'logout'].includes(operation) && op.method !== 'GET') headers['Idempotency-Key'] = randomUUID()
  const search = new URLSearchParams(Object.entries(query).map(([key, value]) => [key, String(value)]))
  const response = await fetch(base + path + (search.size ? '?' + search : ''), { method: op.method, headers, body: body === undefined ? undefined : JSON.stringify(body) }), payload = await response.json()
  evidence.controlRequests.push({ base, operation, method: op.method, path, status: response.status, code: payload.code ?? null, requestId: payload.meta?.request_id ?? payload.request_id ?? null })
  if (!response.ok) throw new Error(operation + ' HTTP' + response.status + ' ' + String(payload.code))
  checkSchema(op.responses[String(response.status)].content['application/json'].schema, payload, operation + ' response')
  return payload.data
}
async function sourceIdentity(commit, prefix, directory) {
  const files = execFileSync('/usr/bin/git', ['ls-tree', '-r', '--name-only', commit, prefix], { encoding: 'utf8' }).trim().split('\n'), hashes = {}
  for (const file of files) {
    const relative = prefix === 'frontend' ? file : file.slice('backend/'.length)
    const actual = await readFile(resolve(directory, relative)), expected = execFileSync('/usr/bin/git', ['show', commit + ':' + file])
    if (sha(actual) !== sha(expected)) throw new Error('Source identity mismatch: ' + file)
    hashes[file] = sha(actual)
  }
  return hashes
}
async function capture(page, name) {
  await page.evaluate(async () => { await document.fonts.ready; await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))); await Promise.all(document.getAnimations().filter(animation => animation.effect?.getComputedTiming().iterations !== Infinity).map(animation => animation.finished.catch(() => {}))) })
  const file = name + '.png'; await page.screenshot({ path: resolve(output, file), animations: 'disabled' }); evidence.screenshots.push(file)
  evidence.layouts.push(await page.evaluate(label => ({ label, width: innerWidth, scrollWidth: document.documentElement.scrollWidth }), name))
}
async function historyCard(page, id, expected) {
  await page.getByRole('tab', { name: '变更与排期差异', exact: true }).click()
  const card = page.locator('.el-drawer:visible .business-card').filter({ has: page.locator('.record-meta > span').filter({ hasText: new RegExp('^编号\\s*' + id + '$') }) })
  await card.waitFor(); const details = card.locator('details')
  if (await details.getAttribute('open') === null) await details.locator('summary').click()
  const reason = card.locator('[data-plan-reason] dd'); await reason.waitFor()
  if (await reason.textContent() !== expected) throw new Error('Displayed history reason differs from original text')
  if (await card.locator('[data-plan-reason-missing], img, script').count()) throw new Error('Verified reason missing or treated as HTML')
  for (const label of ['原因与决定依据', '操作者', '创建时间', '变更前', '变更后', '证据']) if (!(await card.textContent()).includes(label)) throw new Error('Lost audit context ' + label)
  return { card, reason }
}
try {
  evidence.sourceChecks.frontend = await sourceIdentity(frontendSource, 'frontend', process.cwd())
  evidence.sourceChecks.backend = await sourceIdentity(backendSource, 'backend/t44', resolve('..', '.runtime/plan-reason-api/source/backend'))
  token = (await call('login', {}, { username: credential.manager.username, password: credential.manager.password })).access_token
  const project = await call('createProject', {}, { name: '[synthetic][frontend UI003] ' + new Date().toISOString() + '-' + randomUUID().slice(0, 6), description: 'Owned literal reason verification, not independent acceptance.' }); evidence.resources.project = { id: project.id, name: project.name }
  if (project.id === 41) throw new Error('Refusing old fixture41')
  const params = { project_id: project.id }, owner = credential.developer
  await call('addProjectMember', params, { username: owner.username, roles: [2], reason: 'Synthetic UI003 project-only developer role' })
  const start = Math.ceil(Date.now() / 3600000) * 3600000 + 2 * 86400000, iso = offset => new Date(start + offset).toISOString()
  const iteration = await call('createIteration', params, { name: 'Synthetic UI003 iteration', planned_start: iso(0), planned_end: iso(10 * 86400000), capacity: [{ user_id: owner.user_id, available_hours: 8 }], buffer_hours: 1, delay_contingency: 'Keep all new records for audit review' }); evidence.resources.iteration_id = iteration.id
  let task = (await call('createTask', params, { title: 'Synthetic UI003 literal history', description: 'Dedicated new fixture only', owner_id: owner.user_id, iteration_id: iteration.id, dependency_task_ids: [], plan: { planned_start: iso(3600000), planned_end: iso(8 * 3600000), estimated_hours: 2, buffer_hours: 0.5, delay_contingency: 'Preserve original evidence' } })).task
  evidence.resources.task_id = task.id; evidence.resources.initialTask = task
  const proof = [{ kind: 3, locator: 'https://example.com/t44/frontend-ui003', description: 'Synthetic literal history evidence' }]
  const legacyReason = 'changeTaskPlan'
  const legacy = await call('changeTaskPlan', { ...params, task_id: task.id }, { expected_version: task.version, plan: { ...task.plan, planned_end: iso(86400000) }, reason: legacyReason, evidence: proof }, legacyBase); task = legacy.task
  const auditQuery = { task_id: task.id, page: 1, page_size: 100 }
  const raw = (await call('listProjectAuditEvents', params, undefined, legacyBase, auditQuery)).items.find(item => item.id === legacy.audit_id)
  if (!raw || raw.after.some(item => item.field === 'reason')) throw new Error('Legacy endpoint did not expose raw history without reason')
  const projected = (await call('listProjectAuditEvents', params, undefined, apiBase, auditQuery)).items.find(item => item.id === legacy.audit_id)
  deepStrictEqual(projected, { ...raw, after: [...raw.after, { field: 'reason', value: legacyReason }] })
  const rawAfter = (await call('listProjectAuditEvents', params, undefined, legacyBase, auditQuery)).items.find(item => item.id === legacy.audit_id); deepStrictEqual(rawAfter, raw)
  evidence.legacy = { audit_id: legacy.audit_id, reason: legacyReason, rawPayloadBeforeSha256: sha(JSON.stringify(raw)), rawPayloadAfterSha256: sha(JSON.stringify(rawAfter)), projected, oldEndpointPayloadUnchanged: true }
  const dependencies = await realpath('frontend/node_modules')
  server = await createServer({ configFile: resolve('frontend/vite.config.ts'), root: resolve('frontend'), cacheDir: resolve('..', '.runtime/frontend-plan-reason/vite-cache-5176'), server: { host: '127.0.0.1', port: 5176, strictPort: true, proxy: { '/api/v1': { target: apiBase, changeOrigin: false } }, fs: { allow: [process.cwd(), dependencies] } } }); await server.listen()
  browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true })
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce', locale: 'zh-CN', timezoneId: 'Asia/Shanghai' }), page = await context.newPage()
    page.on('pageerror', error => evidence.pageErrors.push(error.message)); page.on('response', response => { const path = new URL(response.url()).pathname; if (path.startsWith('/api/v1/')) evidence.browserResponses.push({ width, method: response.request().method(), path, status: response.status(), requestId: response.headers()['x-request-id'] ?? null }) })
    await page.goto(origin + '/tasks'); await page.locator('#login-username').fill(credential.manager.username); await page.locator('#login-password').fill(credential.manager.password); await page.locator('.login-submit').click(); await page.locator('.login-page').waitFor({ state: 'hidden' }); await page.locator('.project-picker select').selectOption(String(project.id)); await page.getByRole('button', { name: task.title, exact: true }).click()
    const legacyView = await historyCard(page, legacy.audit_id, legacyReason); await legacyView.reason.evaluate(element => element.scrollIntoView({ block: 'center' })); await capture(page, `${width}-legacy-literal`)
    const prefix = '2026-10-24T12:34:56Z 是原文，不是时间格式\nchangeTaskPlan\n<img src=x onerror="window.planReasonExecuted=true">\n' + width + ' 原文起点\n', suffix = '\n原文末尾 保留空格  '
    const reasonText = prefix + '保'.repeat(2000 - Array.from(prefix + suffix).length) + suffix; if (reasonText.length !== 2000) throw new Error('Expected exactly2000 BMP characters')
    await writeFile(resolve(output, `${width}-reason.txt`), reasonText)
    await page.getByRole('button', { name: '调整任务排期', exact: true }).click(); const end = new Date(Date.parse(task.plan.planned_end) + 86400000), local = new Date(end.getTime() + 8 * 3600000).toISOString().slice(0, 16)
    await page.locator('#field-plan-planned_end').fill(local); await page.locator('#field-reason').fill(reasonText); if (await page.locator('#field-reason').inputValue() !== reasonText) throw new Error('Input truncated reason')
    await page.locator('#field-evidence-0-kind').selectOption('3'); await page.locator('#field-evidence-0-locator').fill(proof[0].locator); await page.locator('#field-evidence-0-description').fill(proof[0].description)
    const pending = page.waitForResponse(response => new URL(response.url()).pathname === `/api/v1/projects/${project.id}/tasks/${task.id}/plan` && response.request().method() === 'PATCH')
    await page.locator('.operation-form button[type="submit"]').click(); const response = await pending, payload = await response.json(); if (response.status() !== 200) throw new Error('Real plan write HTTP' + response.status())
    checkSchema(operations.changeTaskPlan.responses['200'].content['application/json'].schema, payload, 'Browser plan response')
    const previous = task; task = await call('getTask', { ...params, task_id: task.id }); if (task.version !== previous.version + 1 || task.schedule_version !== previous.schedule_version + 1 || task.owner_id !== previous.owner_id || task.state !== previous.state || task.plan.planned_end !== end.toISOString().replace('.000Z', '.000000Z')) throw new Error('Unexpected plan/state/version result')
    await page.locator('.operation-form').waitFor({ state: 'hidden' })
    const view = await historyCard(page, payload.data.audit_id, reasonText); await view.reason.locator('..').evaluate(element => element.scrollIntoView({ block: 'start' })); await capture(page, `${width}-reason-start`)
    const tail = await view.reason.evaluate(element => { const text = element.firstChild, range = document.createRange(); range.setStart(text, text.length - 30); range.setEnd(text, text.length); const rect = range.getBoundingClientRect(), body = element.closest('.el-drawer__body'); body.scrollTop += rect.bottom - body.getBoundingClientRect().bottom + 20; const visible = range.getBoundingClientRect(), bounds = body.getBoundingClientRect(); return { tailText: range.toString(), visible: visible.top >= bounds.top && visible.bottom <= bounds.bottom } })
    if (!tail.visible) throw new Error('Reason tail not visible after actual scrolling'); await capture(page, `${width}-reason-end`)
    const actual = (await call('listProjectAuditEvents', params, undefined, apiBase, auditQuery)).items.find(item => item.id === payload.data.audit_id); const reasons = actual.after.filter(item => item.field === 'reason'); if (reasons.length !== 1 || reasons[0].value !== reasonText) throw new Error('Actual API reason differs')
    evidence.checks.push({ width, before: { version: previous.version, schedule_version: previous.schedule_version, plan: previous.plan }, after: { version: task.version, schedule_version: task.schedule_version, plan: task.plan }, audit_id: actual.id, requestId: payload.meta.request_id, reasonCodepoints: Array.from(reasonText).length, expectedSha256: sha(reasonText), displayedSha256: sha(await view.reason.textContent()), apiSha256: sha(reasons[0].value), tail, literalHtmlNotExecuted: await page.evaluate(() => window.planReasonExecuted !== true), otherAuditContextRetained: true })
    await page.keyboard.press('Escape'); await page.locator('.task-toolbar').waitFor({ state: 'hidden' }); await page.getByRole('button', { name: '退出', exact: true }).click(); await page.locator('.login-page').waitFor(); await context.close()
  }
  await call('logout'); token = ''
  evidence.passed = !evidence.pageErrors.length && evidence.checks.length === 2 && evidence.checks.every(item => item.expectedSha256 === item.displayedSha256 && item.expectedSha256 === item.apiSha256 && item.literalHtmlNotExecuted) && evidence.layouts.every(item => item.scrollWidth <= item.width)
  if (!evidence.passed) process.exitCode = 1
} catch (error) { evidence.passed = false; evidence.failure = error.message; process.exitCode = 1 }
finally { if (browser) await browser.close(); if (server) await server.close(); evidence.finishedAt = new Date().toISOString(); evidence.ownBrowserAnd5176Closed = true; await writeFile(resolve(output, 'results.json'), JSON.stringify(evidence, null, 2) + '\n'); console.log(JSON.stringify(evidence)) }
