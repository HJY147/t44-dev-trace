<script setup lang="ts">
import { computed, onUnmounted, ref, shallowRef } from 'vue'
import { ElButton, ElDialog } from 'element-plus'
import { api, ApiError, intentFor, request } from '../api'
import type { Intent } from '../api'
import { asArray, asRow, initial, label, operationLabels, resolve, schemas, validate } from '../contract'
import type { Json, Row } from '../contract'
import { display, workspace } from '../workspace'
import FieldEditor from './FieldEditor.vue'

const props = defineProps<{ operation: string; schemaName: string; params: Row; preset: Row; refresh: () => Promise<Row | void>; saved: (data: Row) => Promise<void> }>()
const emit = defineEmits<{ close: [] }>()
const schema = computed(() => {
  const original = schemas[props.schemaName]!
  return props.schemaName === 'ReviewCreate' ? { ...original, properties: { ...original.properties, checklist: { ...resolve(original.properties!.checklist!), minItems: asArray(workspace.template.items).length, maxItems: asArray(workspace.template.items).length } } } : original
})
const draft = shallowRef<Json>({ ...asRow(initial(schema.value)), ...JSON.parse(JSON.stringify(props.preset)) })
const errors = ref<Record<string, string>>({})
const failure = ref<ApiError | null>(null)
const busy = ref(false)
const intent = ref<Intent>()
const currentVersion = ref<number | null>(null)
let active = true
onUnmounted(() => { active = false })
const title = computed(() => operationLabels[props.operation] ?? '保存记录')
async function submit(checkOnly = false): Promise<void> {
  if (!active) return
  errors.value = validate(props.schemaName, draft.value)
  if (Object.keys(errors.value).length) return
  busy.value = true; failure.value = null
  const token = api.token
  const current = () => active && api.token === token
  try {
    if (checkOnly) {
      const category = props.operation === 'createTask' ? 1 : props.operation === 'transitionTask' ? 2 : 3
      await request('validateContractPayload', props.params, {}, { category, ...(category === 1 ? {} : { task_id: props.params.task_id! }), payload: draft.value })
      if (!current()) return
      workspace.notice = '填写检查通过；操作是否可以执行，仍需正式提交后确认。'; return
    }
    intent.value = intentFor(props.operation, props.params, draft.value, intent.value)
    const result = await request(props.operation, props.params, {}, draft.value, intent.value)
    if (!current()) return
    workspace.notice = `${title.value}已完成${result.meta.replayed ? '（原请求结果已确认）' : ''}，正在读取最新记录。`
    await props.saved(asRow(result.data))
    if (!current()) return
    const action = props.operation === 'transitionTask' ? display(asRow(draft.value).action, 'action') : title.value
    workspace.notice = result.meta.replayed ? `${action}的历史结果已确认，最新记录已刷新。请以详情中的当前状态为准。` : `${action}已完成，最新记录已刷新。`
    emit('close')
  } catch (cause) {
    if (!current()) return
    failure.value = cause instanceof ApiError ? cause : new ApiError(0, { message: '最新记录暂时无法读取，请刷新确认。' })
    errors.value = Object.fromEntries(asArray(failure.value.detail.violations).map(asRow).map((v) => [String(v.path), String(v.message ?? '请检查此字段')]))
    if ([403, 409].includes(failure.value.status)) {
      const fresh = await props.refresh().catch(() => undefined)
      if (!current()) return
      const version = fresh?.version ?? failure.value.detail.current_version
      currentVersion.value = failure.value.status === 409 && 'expected_version' in asRow(draft.value) && version ? Number(version) : null
    }
  } finally { busy.value = false }
}
function adoptVersion(): void { draft.value = { ...asRow(draft.value), expected_version: currentVersion.value }; currentVersion.value = null; intent.value = undefined }
</script>

<template>
  <ElDialog :model-value="true" :title="title" width="min(780px, calc(100vw - 24px))" :close-on-click-modal="false" :close-on-press-escape="!busy" @update:model-value="!busy && emit('close')">
    <form class="operation-form" @submit.prevent="submit()" novalidate>
      <p class="form-help">请核对记录与版本。操作权限、任务进度、依赖和证据将在提交时检查。</p>
      <div v-if="failure" class="operation-error" role="alert"><strong>{{ failure.status === 403 ? '当前操作无权限' : failure.status === 409 ? '操作被拒绝，已尝试刷新最新记录' : failure.status === 422 ? '请修改提示的字段' : '操作结果需要确认' }}</strong><p>{{ failure.message }}</p><small v-if="failure.detail.request_id">追踪编号：{{ failure.detail.request_id }}</small><p v-if="failure.status === 0 || failure.status === 503">内容未改变时，将按同一操作重试。修改内容会提交新的操作，请先确认原操作结果。</p></div>
      <div v-if="Object.keys(errors).length" class="field-error" role="alert"><p v-for="(message, path) in errors" :key="path">{{ label(String(path).split('/').pop() ?? '') }}：{{ message }}</p></div>
      <button v-if="currentVersion" type="button" class="secondary-button" @click="adoptVersion">采用最新版本 {{ currentVersion }}，保留其余内容</button>
      <FieldEditor v-model="draft" :schema="schema" :errors="errors" />
      <div class="form-actions"><ElButton :disabled="busy" @click="emit('close')">取消</ElButton><ElButton v-if="['createTask', 'transitionTask', 'createReleaseAssessment'].includes(operation)" :disabled="busy" @click="submit(true)">检查填写内容</ElButton><ElButton type="primary" native-type="submit" :loading="busy">{{ failure && [0, 503].includes(failure.status) ? '同一操作重试' : '确认' + title }}</ElButton></div>
    </form>
  </ElDialog>
</template>
