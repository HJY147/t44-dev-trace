import { reactive } from 'vue'
import { api, checkSession, request } from './api'
import { asArray, asRow, beijing, dictionaryFields, operationLabels } from './contract'
import type { Json, Row } from './contract'

export const workspace = reactive({ user: null as Row | null, projectId: null as number | null, project: {} as Row, projects: [] as Row[], members: [] as Row[], iterations: [] as Row[], taskChoices: [] as Row[], dictionaries: {} as Row, template: {} as Row, rules: {} as Row, notice: '', contextWarning: '' })
let contextSequence = 0
function clearContext(): void {
  workspace.project = {}; workspace.members = []; workspace.iterations = []; workspace.taskChoices = []; workspace.template = {}; workspace.rules = {}; workspace.contextWarning = ''
}
function clearSession(notice: string): void {
  contextSequence++; api.token = ''; clearContext()
  workspace.user = null; workspace.projectId = null; workspace.projects = []; workspace.dictionaries = {}; workspace.notice = notice
}
api.unauthorized = () => clearSession('登录已失效，请重新登录。')
export async function allPages(operation: string, params: Row = {}): Promise<Row[]> {
  const items: Row[] = [], token = api.token
  for (let page = 1; ; page++) {
    checkSession(token)
    const data = asRow((await request(operation, params, { page, page_size: 100 })).data)
    checkSession(token)
    const next = asArray(data.items).map(asRow)
    items.push(...next)
    if (items.length >= Number(data.total) || !next.length) return items
  }
}
export async function bootstrap(): Promise<void> {
  const token = api.token
  const [me, dictionaries, projects] = await Promise.all([request('getMe'), request('getDictionaries'), allPages('listProjects')])
  checkSession(token)
  workspace.user = asRow(me.data); workspace.dictionaries = asRow(dictionaries.data); workspace.projects = projects
  if (!projects.some((p) => p.id === workspace.projectId)) workspace.projectId = projects.length ? Number(projects[0]!.id) : null
}
export async function context(): Promise<void> {
  const project_id = workspace.projectId, token = api.token, current = ++contextSequence
  clearContext()
  if (!project_id) return
  const [project, members, iterations] = await Promise.all([request('getProject', { project_id }), allPages('listProjectMembers', { project_id }), allPages('listIterations', { project_id })])
  checkSession(token)
  if (current !== contextSequence || workspace.projectId !== project_id) return
  const [template, rules] = await Promise.allSettled([request('getReviewTemplate', { project_id }), request('getEscalationRules', { project_id })])
  checkSession(token)
  if (current !== contextSequence || workspace.projectId !== project_id) return
  workspace.project = asRow(project.data); workspace.members = members; workspace.iterations = iterations
  workspace.template = template.status === 'fulfilled' ? asRow(template.value.data) : {}
  workspace.rules = rules.status === 'fulfilled' ? asRow(rules.value.data) : {}
  workspace.contextWarning = [template.status === 'rejected' ? '评审模板暂不可用' : '', rules.status === 'rejected' ? '升级规则暂不可用' : ''].filter(Boolean).join('；')
}
const chinese: Record<string, string> = { pending: '待受理', developing: '开发中', blocked: '阻塞', pending_review: '待评审', pending_release: '待上线', delivered: '已交付', rolled_back: '已回滚', manager: '项目经理', developer: '开发人员', reviewer: '评审人员', start: '开始开发', block: '记录阻塞', unblock: '解除阻塞', submit_review: '提交评审', approve_review: '通过评审', reject_review: '退回开发', deliver: '确认交付', rollback: '记录回滚', rework: '决定返工', intake: '受理环节', development: '开发环节', review: '评审环节', release: '上线环节', external_dependency: '外部依赖', pass: '通过', fail: '不通过', reject: '退回', unverified: '未验证', not_applicable: '不适用', data: '数据', permissions: '权限', external_dependencies: '外部依赖', observability: '观测', low: '低', medium: '中', high: '高', approved: '已批准', rejected: '已拒绝', pending_review_assessment: '待审核', repository: '仓库文件', document: '文档', https_url: '网页链接', outbox_pending: '等待投递', mq_confirmed: '已确认投递', inbox_delivered: '通知已送达', fallback_todo: '降级站内待办', accepted: '已接受', due_soon: '临期', overdue: '超期', severely_overdue: '严重超期', owner: '任务负责人', project_managers: '项目经理', human: '人员账号', service: '服务账号', unidentified: '未识别身份' }
export function options(field: string): Row[] {
  return asArray(workspace.dictionaries[dictionaryFields[field] ?? field]).map(asRow).map((entry) => ({ ...entry, label: /[\u3400-\u9fff]/.test(String(entry.label)) ? entry.label! : chinese[String(entry.name)] ?? entry.label! }))
}
export function display(value: Json | undefined, field = ''): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'string') {
    if (field === 'section_id' || field === 'item_id') return String(asArray(workspace.template[field === 'section_id' ? 'sections' : 'items']).map(asRow).find((item) => item[field] === value)?.title ?? value)
    if (['recipient_kinds', 'actor_kind', 'disposition', 'selection'].includes(field)) return chinese[value] ?? value
    if (/^\d{4}-\d\d-\d\dT/.test(value)) return beijing(value)
    return operationLabels[value] ?? value
  }
  if (['owner_id', 'user_id', 'responsible_user_id'].includes(field)) return String(asRow(workspace.members.find((m) => asRow(m.user).id === value)?.user).display_name ?? value)
  const dictionary = field === 'blocked_from_state' || field.endsWith('_state') ? options('state') : options(field)
  return String(dictionary.find((entry) => entry.value === value)?.label ?? value)
}
export async function logout(): Promise<void> {
  await request('logout')
  clearSession('已退出当前会话。')
}
