import { vi } from 'vitest'
import frozen from '../../specs/contracts/openapi.json'
import { asRow, schemas } from '../../frontend/src/contract'
import type { Json, Row } from '../../frontend/src/contract'
import { api } from '../../frontend/src/api'
import { workspace } from '../../frontend/src/workspace'
export const user: Row = { id: 1, username: 'fixture-user', display_name: '夹具用户' }
export const project: Row = { id: 1, name: '夹具项目', description: '仅模块测试使用', version: 1, my_roles: [1, 2, 3], created_by: 1, created_at: '2026-10-23T00:00:00Z' }
export const plan: Row = { planned_start: '2026-10-23T00:00:00Z', planned_end: '2026-10-24T00:00:00Z', estimated_hours: 8, buffer_hours: 2, delay_contingency: '由经理记录新计划与依据' }
export const iteration: Row = { id: 1, project_id: 1, version: 3, plan_version: 2, plan: { name: '夹具迭代', planned_start: plan.planned_start!, planned_end: plan.planned_end!, buffer_hours: 2, delay_contingency: '由经理记录新计划与依据', capacity: [{ user_id: 1, available_hours: 8 }] }, created_at: '2026-10-23T00:00:00Z', updated_at: '2026-10-23T00:00:00Z' }
export const member: Row = { user, project_id: 1, roles: [1, 2, 3], version: 1, active: true }
export const task: Row = { id: 1, project_id: 1, iteration_id: 1, title: '夹具交付任务', description: '可追踪 fetch 夹具，不是后端数据', owner_id: 1, state: 2, version: 1, schedule_version: 1, delivery_cycle: 1, review_cycle: 1, plan, blocked_from_state: null, block_reason: null, responsibility_stage: null, latest_review_id: null, approved_review_id: null, approved_assessment_id: null, approved_assessment_version: null, escalation_count: 0, created_at: '2026-10-23T00:00:00Z', updated_at: '2026-10-23T00:00:00Z', artifact_revision: 'a'.repeat(40) }
export const evidence: Row = { kind: 3, locator: 'https://example.com/evidence', description: '模块测试证据' }
export const notification: Row = { id: 1, project_id: 1, task_id: 1, event_id: 1, recipient_id: 1, version: 1, level: 2, title: '夹具提醒', message: '仅通知测试', fallback: true, read_at: null, handled_at: null, handling_note: null, created_at: '2026-10-23T00:00:00Z' }
export const template = frozen.components.schemas.ReviewTemplate.examples[0] as unknown as Row
const enums: Record<string, string> = { task_states: 'TaskState', project_roles: 'ProjectRole', transition_actions: 'TransitionAction', responsibility_stages: 'ResponsibilityStage', review_judgments: 'ReviewItemJudgment', review_verdicts: 'ReviewVerdict', risk_perspectives: 'RiskPerspective', risk_severities: 'RiskSeverity', escalation_levels: 'EscalationLevel', delivery_dispositions: 'DeliveryDisposition', evidence_kinds: 'EvidenceRef', assessment_statuses: 'AssessmentStatus', audit_outcomes: 'AuditOutcome' }
export const dictionaries: Row = Object.fromEntries(Object.entries(enums).map(([key, name]) => {
  const schema = name === 'EvidenceRef' ? schemas.EvidenceRef!.properties!.kind! : schemas[name]!
  const source = schema as typeof schema & { 'x-enum-names': string[] }
  return [key, (source.enum ?? [1, 2, 3]).map((value, index) => ({ value, name: source['x-enum-names']?.[index] ?? `fixture_${value}`, label: key === 'task_states' ? ['待受理', '开发中', '阻塞', '待评审', '待上线', '已交付', '已回滚'][index]! : key === 'transition_actions' ? ['开始开发', '记录阻塞', '解除阻塞', '提交评审', '通过评审', '退回开发', '确认交付', '记录回滚', '决定返工'][index]! : `夹具${key}${value}` }))]
}))
export const page = (items: Row[]): Row => ({ items, total: items.length, page: 1, page_size: 20 })
export const envelope = (data: Json, replayed = false) => ({ data, meta: { replayed, request_id: 'fixture-request', contract_version: '1.0.0', server_time: '2026-10-23T00:00:00Z', original_request_id: replayed ? 'original-fixture' : null } })
export function seed(): void {
  Object.assign(workspace, { user, projectId: 1, project, projects: [project], members: [member], iterations: [iteration], dictionaries, template, rules: { version: 1, scan_interval_seconds: 60, rules: [] }, taskChoices: [task], notice: '', contextWarning: '' })
  api.token = 'fixture-token-not-a-real-credential'
}
export function fixtureFetch(overrides: Record<string, Json> = {}) {
  const calls: { path: string; method: string; body: Row; headers: Record<string, string> }[] = []
  const fetcher = vi.fn(async (url: string | URL | Request, init?: RequestInit) => {
    const path = String(url).split('?')[0]!, method = init?.method ?? 'GET', body = init?.body ? JSON.parse(String(init.body)) as Row : {}
    calls.push({ path, method, body, headers: init?.headers as Record<string, string> })
    let data: Json = {}
    if (path.endsWith('/auth/login')) data = { access_token: 'fixture-token-not-a-real-credential', user, expires_at: '2026-10-23T01:00:00Z', token_type: 'Bearer' }
    else if (path.endsWith('/auth/me')) data = user
    else if (path.endsWith('/dictionaries')) data = dictionaries
    else if (path.endsWith('/review-template')) data = template
    else if (path.endsWith('/escalation-rules')) data = { version: 1, scan_interval_seconds: 60, rules: [] }
    else if (path.endsWith('/members')) data = method === 'GET' ? page([member]) : member
    else if (path.endsWith('/iterations')) data = method === 'GET' ? page([iteration]) : iteration
    else if (path.endsWith('/projects')) data = method === 'GET' ? page([project]) : project
    else if (path.endsWith('/projects/1')) data = project
    else if (path.endsWith('/tasks')) data = method === 'GET' ? page([task]) : task
    else if (path.endsWith('/tasks/1')) data = task
    else if (path.endsWith('/notifications')) data = { ...page([notification]), unread_count: 1, unhandled_count: 1 }
    else if (path.endsWith('/reviews')) data = page([{ id: 1, version: 1, expected_version: 1, title: '夹具评审', sections: template.sections!, checklist: template.items! }])
    else if (path.endsWith('/release-assessments')) data = page([{ id: 1, version: 1, title: '夹具上线预案', status: 1 }])
    else if (path.endsWith('/dependencies')) data = page([{ id: 1, depends_on_task_id: 2, satisfied: false }])
    else if (path.endsWith('/decisions')) data = page([{ id: 1, reason: '夹具决定依据', evidence: [evidence] }])
    else if (path.endsWith('/audit-events')) data = page([{ id: 1, operation_id: 'changeTaskPlan', before: [{ field: 'planned_end', value: '旧计划' }], after: [{ field: 'planned_end', value: '新计划' }], evidence: [evidence] }])
    else if (path.endsWith('/escalations')) data = page([{ id: 1, level: 2, task_id: 1, recipient_ids: [1], handled_count: 0 }])
    if (path in overrides) data = overrides[path]!
    return new Response(JSON.stringify(envelope(data)), { status: 200, headers: { 'Content-Type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fetcher)
  return { calls, fetcher }
}
export const copy = (value: Json): Row => asRow(JSON.parse(JSON.stringify(value)) as Json)
