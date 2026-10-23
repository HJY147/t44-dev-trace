<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { ElButton, ElDrawer } from 'element-plus'
import { api, ApiError, request } from '../api'
import { asArray, asRow } from '../contract'
import type { Row } from '../contract'
import type { WorkspacePage } from '../navigation'
import { bootstrap, context, options, workspace } from '../workspace'
import { formSchemas, presets } from '../forms'
import DataState from '../components/DataState.vue'
import OperationForm from '../components/OperationForm.vue'
import PageHeading from '../components/PageHeading.vue'
import RecordList from '../components/RecordList.vue'
import RecordView from '../components/RecordView.vue'
import TaskDrawer from '../components/TaskDrawer.vue'
const props = defineProps<{ page: WorkspacePage }>()
const titles: Record<WorkspacePage, [string, string]> = { overview: ['工作台', '查看当前项目的真实任务与协作进展。'], projects: ['项目空间', '选择参与的项目，管理成员与协作责任。'], tasks: ['交付任务', '推进交付状态，记录阻塞、评审与每一次决定。'], schedule: ['迭代排期', '安排人力容量、计划时间、缓冲与延期预案。'], reviews: ['评审与发布', '打开任务，记录评审证据、上线风险与回滚预案。'], notifications: ['通知中心', '阅读与处理分别留痕，处理提醒不会自动解除阻塞。'], audit: ['审计记录', '追溯操作结果、变更前后差异和决定依据。'] }
const pageNumber = ref(1), filter = ref(''), taskFilter = ref(''), section = ref('notifications')
const data = ref<Row>({ items: [], total: 0 })
const busy = ref(false), failure = ref<ApiError | null>(null), memberDrawer = ref(false), selectedTask = ref<number | null>(null), revision = ref(0)
const taskDrawer = ref<InstanceType<typeof TaskDrawer>>()
const form = ref<{ operation: string; schemaName: string; params: Row; preset: Row } | null>(null)
const rows = computed(() => asArray(data.value.items).map(asRow))
const needsProject = computed(() => !['projects', 'notifications'].includes(props.page))
const taskPage = computed(() => ['overview', 'tasks', 'reviews'].includes(props.page))
let sequence = 0
let active = true
onUnmounted(() => { active = false; sequence++ })
async function refresh(reloadContext = false): Promise<void> {
  if (!active || !workspace.user) return
  const current = ++sequence; busy.value = true; failure.value = null; data.value = { items: [], total: 0 }
  try {
    if (reloadContext) await context()
    if (current !== sequence || !workspace.user) return
    if (needsProject.value && !workspace.projectId) return
    const params: Row = { project_id: workspace.projectId }, query: Row = { page: pageNumber.value, page_size: 20 }
    const operation = taskPage.value ? 'listTasks' : props.page === 'projects' ? 'listProjects' : props.page === 'schedule' ? 'listIterations' : props.page === 'audit' ? 'listProjectAuditEvents' : section.value === 'escalations' ? 'listEscalations' : 'listMyNotifications'
    if (filter.value) query[taskPage.value ? 'state' : props.page === 'audit' ? 'outcome' : 'handled'] = taskPage.value || props.page === 'audit' ? Number(filter.value) : filter.value === 'true'
    if (taskFilter.value && (props.page === 'audit' || props.page === 'notifications' && section.value === 'escalations')) query.task_id = Number(taskFilter.value)
    if (props.page === 'notifications') {
      if (section.value === 'rules') { if (!workspace.rules.version) throw new ApiError(503, { message: '升级规则暂不可用，请稍后刷新。' }); data.value = workspace.rules; return }
      if (section.value === 'escalations' && !workspace.projectId) return
      if (section.value === 'notifications' && workspace.projectId) query.project_id = workspace.projectId
      if (section.value === 'escalations') delete query.handled
    }
    const result = asRow((await request(operation, params, query)).data)
    if (current === sequence) { data.value = result; if (taskPage.value) workspace.taskChoices = asArray(result.items).map(asRow) }
  } catch (cause) { if (current === sequence) failure.value = cause as ApiError }
  finally { if (current === sequence) busy.value = false }
}
watch(() => [workspace.user, workspace.projectId], () => { selectedTask.value = null; pageNumber.value = 1; if (!workspace.user) { form.value = null; memberDrawer.value = false; data.value = { items: [], total: 0 }; sequence++ } else refresh(true) }, { immediate: true })
watch(() => [pageNumber.value, filter.value, section.value], () => refresh())
function open(operation: string, record: Row = {}): void {
  form.value = { operation, schemaName: formSchemas[operation]!, params: { project_id: record.project_id ?? workspace.projectId, ...(record.user ? { user_id: asRow(record.user).id! } : {}), ...(operation === 'changeIteration' ? { iteration_id: record.id! } : {}), ...(['markNotificationRead', 'handleNotification'].includes(operation) ? { notification_id: record.id! } : {}) }, preset: presets(operation, record) }
}
async function saved(record: Row): Promise<void> {
  if (!active) return
  const token = api.token
  if (form.value?.operation === 'createProject') { await bootstrap(); if (!active || api.token !== token) return; workspace.projectId = Number(record.id) }
  revision.value++; await refresh(true)
  if (active && api.token === token) await taskDrawer.value?.refresh()
}
async function refreshConflict(): Promise<Row> {
  if (!active) return {}
  const token = api.token
  revision.value++; await Promise.all([refresh(true), taskDrawer.value?.refresh()])
  if (!active || api.token !== token) return {}
  if (taskDrawer.value) return taskDrawer.value.task
  const params = form.value?.params ?? {}
  return workspace.members.find((m) => asRow(m.user).id === params.user_id) ?? workspace.iterations.find((i) => i.id === params.iteration_id) ?? rows.value.find((r) => r.id === params.notification_id) ?? {}
}
async function notificationTask(row: Row): Promise<void> { workspace.projectId = Number(row.project_id); await nextTick(); selectedTask.value = Number(row.task_id) }
</script>
<template>
  <PageHeading :title="titles[page][0]" :description="titles[page][1]" eyebrow="研发交付 / WORKSPACE"><ElButton :loading="busy" @click="refresh(true)">刷新记录</ElButton></PageHeading>
  <div v-if="workspace.notice" class="inline-notice" role="status"><span>{{ workspace.notice }}</span><button class="text-button" aria-label="关闭提示" @click="workspace.notice = ''">×</button></div>
  <p v-if="workspace.contextWarning && ['reviews', 'notifications'].includes(page)" class="form-help">{{ workspace.contextWarning }}；其他功能仍可使用。</p>
  <div v-if="page === 'overview' && workspace.projectId" class="metric-grid"><article v-for="[name, value] in [['参与项目', workspace.projects.length], ['项目任务', data.total ?? '—'], ['项目成员', workspace.members.length], ['迭代安排', workspace.iterations.length]]" :key="String(name)" class="metric-card"><p>{{ name }}</p><p class="metric-card__value">{{ value }}</p><p class="metric-card__hint">当前工作空间记录</p></article></div>
  <section class="surface business-panel">
    <div class="business-toolbar">
      <template v-if="page === 'projects'"><ElButton type="primary" @click="open('createProject')">创建项目</ElButton><ElButton :disabled="!workspace.projectId" @click="memberDrawer = true">管理当前项目成员</ElButton></template>
      <ElButton v-if="page === 'schedule'" type="primary" :disabled="!workspace.projectId" @click="open('createIteration')">新建迭代与容量</ElButton>
      <ElButton v-if="taskPage" type="primary" :disabled="!workspace.projectId" @click="open('createTask')">登记交付任务</ElButton>
      <label v-if="taskPage || page === 'audit'" class="compact-filter">{{ taskPage ? '任务状态' : '执行结果' }}<select v-model="filter" @change="pageNumber = 1"><option value="">全部</option><option v-for="entry in options(taskPage ? 'state' : 'outcome')" :key="String(entry.value)" :value="String(entry.value)">{{ entry.label }}</option></select></label>
      <template v-if="page === 'notifications'"><div class="business-tabs" role="tablist" aria-label="通知与升级"><button v-for="[key, text] in [['notifications', '个人通知'], ['escalations', '项目升级历史'], ['rules', '升级规则']]" :key="key" role="tab" :aria-selected="section === key" @click="section = key!; pageNumber = 1; filter = ''">{{ text }}</button></div><label v-if="section === 'notifications'" class="compact-filter">处理情况<select v-model="filter"><option value="">全部</option><option value="false">未处理</option><option value="true">已处理</option></select></label></template>
      <label v-if="page === 'audit' || page === 'notifications' && section === 'escalations'" class="compact-filter">任务编号<input v-model="taskFilter" type="number" min="1" @change="pageNumber = 1; refresh()" /></label>
    </div>
    <div v-if="page === 'notifications' && section === 'notifications' && !busy && !failure && workspace.user" class="record-meta" role="status" aria-label="通知统计"><span>未读 {{ data.unread_count }} 条</span><span>未处理 {{ data.unhandled_count }} 条</span></div>
    <DataState v-if="busy" kind="loading" />
    <DataState v-else-if="failure" kind="error" :http-status="failure.status" :description="failure.message" refreshable @refresh="refresh(true)" />
    <DataState v-else-if="needsProject && !workspace.projectId || page === 'notifications' && section !== 'notifications' && !workspace.projectId" kind="empty" title="先选择一个项目" description="在顶部选择参与的项目，或进入项目空间创建项目。" />
    <RecordView v-else-if="page === 'notifications' && section === 'rules'" :value="data" />
    <DataState v-else-if="!rows.length" kind="empty" title="暂无相关记录" description="可以调整筛选，或使用上方操作开始登记。" />
    <RecordList v-else :rows="rows" :total="Number(data.total)" :page="pageNumber" :clickable="taskPage" @page="pageNumber = $event" @select="selectedTask = Number($event.id)">
      <template #default="{ row }"><div class="record-actions"><ElButton v-if="page === 'projects'" @click="workspace.projectId = Number(row.id)">{{ workspace.projectId === row.id ? '当前项目' : '选择项目' }}</ElButton><ElButton v-if="page === 'schedule'" @click="open('changeIteration', row)">调整迭代与容量</ElButton><template v-if="page === 'notifications' && section === 'notifications'"><ElButton :disabled="Boolean(row.read_at)" @click="open('markNotificationRead', row)">标记已读</ElButton><ElButton :disabled="Boolean(row.handled_at)" @click="open('handleNotification', row)">记录处理结果</ElButton><ElButton @click="notificationTask(row)">查看相关任务</ElButton></template></div></template>
    </RecordList>
  </section>
  <ElDrawer v-model="memberDrawer" title="项目成员与角色" size="min(700px, 100vw)"><ElButton type="primary" @click="open('addProjectMember')">添加已有账号</ElButton><RecordList :rows="workspace.members" :total="workspace.members.length" :page="1" :page-size="Math.max(1, workspace.members.length)"><template #default="{ row }"><div class="record-actions"><ElButton @click="open('changeProjectMember', row)">调整角色</ElButton><ElButton @click="open('removeProjectMember', row)">移除成员</ElButton></div></template></RecordList></ElDrawer>
  <TaskDrawer v-if="selectedTask && workspace.projectId" ref="taskDrawer" :task-id="selectedTask" :project-id="workspace.projectId" :revision="revision" @close="selectedTask = null" @operate="(operation, schemaName, params, preset) => form = { operation, schemaName, params, preset }" />
  <OperationForm v-if="form" :key="form.operation + form.schemaName" v-bind="form" :refresh="refreshConflict" :saved="saved" @close="form = null" />
</template>
