import frozen from '../../specs/contracts/openapi.json'
import Ajv2020 from 'ajv/dist/2020'
import addFormats from 'ajv-formats'

export type Json = null | boolean | number | string | Json[] | Row
export type Row = { [key: string]: Json }
export type Schema = { $ref?: string; type?: string; properties?: Record<string, Schema>; required?: string[]; items?: Schema; oneOf?: Schema[]; anyOf?: Schema[]; enum?: (string | number)[]; const?: Json; format?: string; minItems?: number; maxItems?: number; minimum?: number; maximum?: number; maxLength?: number; multipleOf?: number }
type Operation = { operationId: string; requestBody?: { content: { 'application/json': { schema: Schema } } } }
const spec = frozen as unknown as { components: { schemas: Record<string, Schema> }; paths: Record<string, Record<string, Operation>> }
export const operations = Object.fromEntries(Object.entries(spec.paths).flatMap(([path, methods]) => Object.entries(methods).map(([method, item]) => [item.operationId, { path, method: method.toUpperCase(), schema: item.requestBody?.content['application/json'].schema }])))
export const schemas = spec.components.schemas
export const asRow = (value: Json | undefined): Row => value && typeof value === 'object' && !Array.isArray(value) ? value : {}
export const asArray = (value: Json | undefined): Json[] => Array.isArray(value) ? value : []
export const resolve = (schema: Schema): Schema => schema.$ref ? resolve(schemas[schema.$ref.split('/').pop()!]!) : schema.anyOf ? resolve(schema.anyOf.find((part) => part.type !== 'null')!) : schema
export const initial = (schema: Schema): Json => {
  if (schema.anyOf?.some((part) => part.type === 'null')) return null
  const s = resolve(schema)
  if (s.const !== undefined) return s.const
  if (s.enum) return null
  if (s.type === 'object') return Object.fromEntries(Object.entries(s.properties ?? {}).map(([key, part]) => [key, initial(part)]))
  if (s.type === 'array') return Array.from({ length: s.minItems ?? 0 }, () => initial(s.items!))
  if (s.type === 'number' || s.type === 'integer') return null
  if (s.type === 'boolean') return false
  return ''
}
const validator = new Ajv2020({ strict: false, allErrors: true })
addFormats(validator)
validator.addSchema({ components: spec.components }, 'frozen')
const validations = new Map<string, ReturnType<typeof validator.compile>>()
export function validate(name: string, value: Json): Record<string, string> {
  if (!validations.has(name)) validations.set(name, validator.compile({ $ref: `frozen#/components/schemas/${name}` }))
  const check = validations.get(name)!
  if (check(value)) return {}
  return Object.fromEntries((check.errors ?? []).map((e) => [e.instancePath + (e.keyword === 'required' ? '/' + String(e.params.missingProperty) : ''), `${label(String(e.params.missingProperty ?? e.instancePath.split('/').pop() ?? '字段'))}：请检查必填项、格式、范围或证据是否完整`]))
}
export const dictionaryFields: Record<string, string> = { state: 'task_states', roles: 'project_roles', action: 'transition_actions', responsibility_stage: 'responsibility_stages', judgment: 'review_judgments', verdict: 'review_verdicts', perspective: 'risk_perspectives', severity: 'risk_severities', level: 'escalation_levels', kind: 'evidence_kinds', status: 'assessment_statuses', outcome: 'audit_outcomes', delivery_disposition: 'delivery_dispositions', decision_type: 'decision_types', my_roles: 'project_roles' }
export const labels: Record<string, string> = {
  name: '名称', title: '标题', description: '说明', username: '账号',
  password: '密码', roles: '项目角色', my_roles: '我的角色', reason: '原因与决定依据',
  expected_version: '提交版本', version: '记录版本', plan: '交付计划', new_plan: '返工新计划',
  planned_start: '计划开始', planned_end: '计划结束', estimated_hours: '预估工时', buffer_hours: '缓冲工时',
  delay_contingency: '延期预案', capacity: '人力容量', available_hours: '可用工时', user_id: '成员',
  owner_id: '任务负责人', iteration_id: '所属迭代', dependency_task_ids: '前置任务编号', depends_on_task_id: '前置任务编号',
  evidence: '证据', kind: '证据类型', locator: '证据位置', revision: '固定版本',
  action: '操作', basis: '解除依据', responsibility_stage: '责任环节', artifact_revision: '审核对象提交 SHA',
  review_id: '评审编号', review_version: '评审版本', assessment_id: '评估编号', assessment_version: '评估版本',
  expected_assessment_version: '评估提交版本', release_version: '发布版本', target_version: '回滚目标版本', rollback_plan_version: '预案版本',
  impact: '影响范围', sections: '八段式评审记录', section_id: '评审段落', content: '记录内容',
  checklist: '逐项评审清单', item_id: '评审项', judgment: '单项判定', rationale: '判定依据',
  verdict: '评审结论', template_version: '模板版本', risks: '四视角上线风险', perspective: '风险视角',
  severity: '风险级别', risk: '风险描述', mitigation: '应对措施', rollback_plan: '回滚预案',
  trigger: '触发条件', steps: '执行步骤', verification: '回滚验证', responsible_user_id: '回滚负责人',
  note: '处理说明', id: '编号', project_id: '项目编号', task_id: '任务编号',
  user: '成员资料', display_name: '姓名', active: '有效成员', state: '任务状态',
  status: '评估情况', blocked_from_state: '阻塞前状态', block_reason: '阻塞原因', schedule_version: '排期版本',
  delivery_cycle: '交付轮次', review_cycle: '评审轮次', escalation_count: '升级次数', created_at: '创建时间',
  updated_at: '更新时间', created_by: '创建人', approved_review_id: '有效代码评审', latest_review_id: '最新代码评审',
  approved_assessment_id: '有效上线评估', approved_assessment_version: '有效评估版本', reviewed_by: '预案审核人', reviewed_at: '预案审核时间',
  review_evidence: '预案审核证据', review_reason: '预案审核依据', event_id: '升级事件', recipient_id: '收件人',
  recipient_ids: '收件人', level: '提醒级别', message: '提醒内容', fallback: '已降级站内待办',
  read_at: '阅读时间', handled_at: '处理时间', handling_note: '处理说明', handled_count: '已处理人数',
  operation_id: '操作', actor_id: '操作者', actor_kind: '身份类型', request_id: '追踪编号',
  outcome: '执行结果', reason_code: '结果说明', observed_version: '实际版本', before: '变更前',
  after: '变更后', value: '记录值', evidence_required_for_pass: '通过须有证据', required: '必需项',
  effective_at: '生效时间', decided_by: '决定人', source: '规则依据', items: '记录',
  scan_interval_seconds: '扫描间隔（秒）', rules: '升级规则', recipient_kinds: '接收角色', priority: '优先级',
  start_offset_seconds: '起始偏移秒', end_offset_seconds: '结束偏移秒', start_inclusive: '含起点', end_inclusive: '含终点',
  rule_version: '规则版本', scan_run_id: '扫描批次', decision: '决定记录', audit_id: '审计编号',
  code: '结果代码', valid: '结构有效', category: '校验类别', payload: '待校验内容',
  total: '总数', page: '页码', page_size: '每页数量', original_request_id: '原请求编号',
  contract_version: '契约版本', server_time: '服务端时间', replayed: '原请求重放', task: '交付任务',
  assessment: '上线评估', review: '代码评审', dependency: '依赖', created: '新建记录',
  unread_count: '未读', unhandled_count: '未处理', label: '名称', decided_at: '决定时间',
  task_version: '任务版本', rule: '规则', current_version: '当前版本', current_state: '当前状态',
  original_error_code: '原结果代码', violations: '字段提示', path: '字段位置', event: '升级事件',
  expires_at: '有效期', token_type: '凭据类型', plan_version: '计划版本',
}
Object.assign(labels, { reviewer_id: '评审人', satisfied: '依赖已满足', disposition: '投递情况', selection: '规则选择', type: '类别', schema_version: '填写规则版本', business_guards_executed: '已检查执行条件', validated_operation_id: '已检查的操作' })
export const label = (key: string): string => labels[key] ?? '补充信息'
export const operationLabels: Record<string, string> = { createProject: '创建项目', addProjectMember: '添加成员', changeProjectMember: '调整成员角色', removeProjectMember: '移除成员', createIteration: '新建迭代', changeIteration: '调整迭代与容量', createTask: '登记交付任务', changeTaskPlan: '调整任务排期', changeTaskAssignment: '调整任务负责人', addTaskDependency: '添加前置依赖', removeTaskDependency: '移除前置依赖', transitionTask: '推进交付任务', createTaskReview: '发布代码评审记录', createReleaseAssessment: '登记上线评估与回滚预案', reviewReleaseAssessment: '审核上线预案', markNotificationRead: '标记通知已读', handleNotification: '记录通知处理结果' }
export function safeLink(value: string): string | null {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : null } catch { return null }
}
export const beijing = (value: string): string => new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
