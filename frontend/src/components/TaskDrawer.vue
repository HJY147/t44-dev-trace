<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElButton, ElDrawer } from 'element-plus'
import { ApiError, request } from '../api'
import { asArray, asRow } from '../contract'
import type { Row } from '../contract'
import { options, workspace } from '../workspace'
import { formSchemas, presets, transitionSchema } from '../forms'
import DataState from './DataState.vue'
import RecordList from './RecordList.vue'
import RecordView from './RecordView.vue'

const props = defineProps<{ projectId: number; taskId: number; revision: number }>()
const emit = defineEmits<{ close: []; operate: [operation: string, schema: string, params: Row, preset: Row] }>()
const task = ref<Row>({})
const tab = ref('detail')
const page = ref(1)
const data = ref<Row>({ items: [], total: 0 })
const busy = ref(false)
const failure = ref<ApiError | null>(null)
const action = ref('')
const tabs: Record<string, [string, string]> = { detail: ['任务概览', ''], dependencies: ['前置依赖', 'listTaskDependencies'], reviews: ['代码评审', 'listTaskReviews'], assessments: ['上线评估与预案', 'listReleaseAssessments'], decisions: ['发布与回滚决定', 'listTaskDecisions'], escalations: ['升级历史', 'listEscalations'], audit: ['变更与排期差异', 'listProjectAuditEvents'] }
const params = computed(() => ({ project_id: props.projectId, task_id: props.taskId }))
let sequence = 0
async function refresh(): Promise<void> {
  const current = ++sequence; busy.value = true; failure.value = null
  try {
    const result = asRow((await request('getTask', params.value)).data)
    const records = tab.value === 'detail' ? {} : asRow((await request(tabs[tab.value]![1], params.value, { page: page.value, page_size: 20, ...(['escalations', 'audit'].includes(tab.value) ? { task_id: props.taskId } : {}) })).data)
    if (current !== sequence) return
    task.value = result; data.value = records
  } catch (cause) { if (current === sequence) failure.value = cause as ApiError }
  finally { if (current === sequence) busy.value = false }
}
watch(() => [props.taskId, props.revision, tab.value, page.value], refresh, { immediate: true })
function operate(operation: string, row: Row = {}): void {
  const extra: Row = operation === 'removeTaskDependency' ? { dependency_id: row.id! } : operation === 'reviewReleaseAssessment' ? { assessment_id: row.id! } : {}
  emit('operate', operation, formSchemas[operation]!, { ...params.value, ...extra }, presets(operation, row, task.value))
}
function transition(): void {
  if (action.value) emit('operate', 'transitionTask', transitionSchema(Number(action.value)), params.value, { expected_version: task.value.version!, action: Number(action.value) })
}
defineExpose({ refresh, task })
</script>

<template>
  <ElDrawer :model-value="true" :title="String(task.title ?? '交付任务')" size="min(940px, 100vw)" @update:model-value="emit('close')">
    <DataState v-if="busy" kind="loading" />
    <DataState v-else-if="failure" kind="error" :http-status="failure.status" :description="failure.message" refreshable @refresh="refresh" />
    <template v-else>
      <div class="task-toolbar"><label for="task-action">交付操作</label><select id="task-action" v-model="action"><option value="">选择操作</option><option v-for="entry in options('action')" :key="String(entry.value)" :value="String(entry.value)">{{ entry.label }}</option></select><ElButton type="primary" :disabled="!action" @click="transition">填写流转依据</ElButton></div>
      <p class="form-help">操作入口不代表已获批准。任务进度、依赖、责任人与证据将在提交时检查。</p>
      <div class="task-actions"><ElButton @click="operate('changeTaskAssignment')">调整负责人</ElButton><ElButton @click="operate('changeTaskPlan')">调整任务排期</ElButton><ElButton @click="operate('addTaskDependency')">添加前置依赖</ElButton><ElButton :disabled="!workspace.template.version" @click="operate('createTaskReview')">发布代码评审</ElButton><ElButton @click="operate('createReleaseAssessment')">新建上线评估</ElButton></div>
      <div class="business-tabs" role="tablist" aria-label="任务记录"><button v-for="([name], key) in tabs" :key="key" role="tab" :aria-selected="tab === key" @click="tab = key; page = 1">{{ name }}</button></div>
      <RecordView v-if="tab === 'detail'" :value="task" />
      <template v-else><DataState v-if="!asArray(data.items).length" kind="empty" title="此任务暂无相关记录" /><RecordList v-else :rows="asArray(data.items).map(asRow)" :total="Number(data.total)" :page="page" @page="page = $event"><template #default="{ row }"><div class="record-actions"><ElButton v-if="tab === 'dependencies'" @click="operate('removeTaskDependency', row)">移除此依赖</ElButton><ElButton v-if="tab === 'assessments'" @click="operate('reviewReleaseAssessment', row)">审核此预案</ElButton></div></template></RecordList></template>
    </template>
  </ElDrawer>
</template>
