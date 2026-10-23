<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import { asArray, asRow, initial, label, resolve } from '../contract'
import type { Json, Schema } from '../contract'
import { display, options, workspace } from '../workspace'

const props = defineProps({
  schema: { type: Object as PropType<Schema>, required: true },
  modelValue: { type: null as unknown as PropType<Json>, required: true },
  name: { type: String, default: '' },
  path: { type: String, default: '' },
  errors: { type: Object as PropType<Record<string, string>>, default: () => ({}) },
})
const emit = defineEmits<{ 'update:modelValue': [value: Json] }>()
const part = computed(() => resolve(props.schema))
const entries = computed(() => Object.entries(part.value.properties ?? {}))
const object = computed(() => asRow(props.modelValue))
const rows = computed(() => asArray(props.modelValue))
const id = computed(() => 'field' + props.path.replaceAll('/', '-'))
const locked = computed(() => part.value.const !== undefined || ['expected_version', 'expected_assessment_version', 'template_version', 'section_id', 'item_id', 'perspective'].includes(props.name))
const choices = computed(() => {
  if (['owner_id', 'user_id', 'responsible_user_id'].includes(props.name)) return workspace.members.filter((m) => m.active).map((m) => ({ value: asRow(m.user).id, label: asRow(m.user).display_name }))
  if (props.name === 'iteration_id') return workspace.iterations.map((i) => ({ value: i.id, label: asRow(i.plan).name }))
  return options(props.name)
})
const localTime = computed(() => { const time = new Date(String(props.modelValue)).getTime(); return props.modelValue && Number.isFinite(time) ? new Date(time + 8 * 3600_000).toISOString().slice(0, 16) : '' })
const updateObject = (key: string, value: Json) => emit('update:modelValue', { ...object.value, [key]: value })
const updateRow = (index: number, value: Json) => emit('update:modelValue', rows.value.map((v, i) => i === index ? value : v))
function rowTitle(value: Json, index: number): string {
  const row = asRow(value)
  const source = asArray(workspace.template[props.name === 'sections' ? 'sections' : 'items']).map(asRow)
  return String(source.find((item) => item.section_id === row.section_id && row.section_id || item.item_id === row.item_id && row.item_id)?.title ?? `${label(props.name)} ${index + 1}`)
}
function change(event: Event): void {
  const value = (event.target as HTMLInputElement).value
  const time = part.value.format === 'date-time' && value ? new Date(value + '+08:00') : null
  emit('update:modelValue', part.value.type === 'boolean' ? (event.target as HTMLInputElement).checked : part.value.format === 'date-time' ? time && Number.isFinite(time.getTime()) ? time.toISOString() : '' : part.value.type === 'integer' || part.value.type === 'number' ? value === '' ? null : Number(value) : value)
}
</script>

<template>
  <div v-if="part.type === 'object'" class="field-object">
    <div v-for="[key, child] in entries" :key="key" class="form-field" :class="{ 'form-field--nested': ['object', 'array'].includes(resolve(child).type ?? '') }">
      <label :for="'field' + (path + '/' + key).replaceAll('/', '-')">{{ label(key) }}<span v-if="part.required?.includes(key)" class="required-mark" aria-label="必填"> *</span><small v-if="resolve(child).format === 'date-time'">（北京时间）</small></label>
      <FieldEditor :schema="child" :model-value="object[key] ?? null" :name="key" :path="path + '/' + key" :errors="errors" @update:model-value="updateObject(key, $event)" />
    </div>
  </div>
  <div v-else-if="part.type === 'array'" class="array-editor" :id="id">
    <fieldset v-for="(row, index) in rows" :key="index"><legend>{{ rowTitle(row, index) }}</legend><FieldEditor :schema="part.items!" :model-value="row" :name="name" :path="path + '/' + index" :errors="errors" @update:model-value="updateRow(index, $event)" /><button v-if="part.minItems !== part.maxItems" type="button" class="text-button danger" @click="emit('update:modelValue', rows.filter((_, i) => i !== index))">移除这一项</button></fieldset>
    <button v-if="rows.length < (part.maxItems ?? 100) && part.minItems !== part.maxItems" type="button" class="secondary-button" @click="emit('update:modelValue', [...rows, initial(part.items!)])">添加{{ label(name) }}</button>
  </div>
  <div v-else class="field-control">
    <input v-if="locked" :id="id" :value="display(modelValue, name)" readonly class="readonly-field" />
    <input v-else-if="part.type === 'boolean'" :id="id" type="checkbox" :checked="Boolean(modelValue)" @change="change" />
    <select v-else-if="choices.length || part.enum" :id="id" :value="modelValue ?? ''" @change="change"><option value="" disabled>请选择{{ label(name) }}</option><option v-for="choice in choices" :key="String(choice.value)" :value="String(choice.value)">{{ choice.label }}</option></select>
    <template v-else-if="part.type === 'integer' || part.type === 'number'"><input :id="id" type="number" :value="modelValue ?? ''" :min="part.minimum" :max="part.maximum" :step="part.multipleOf ?? (part.type === 'integer' ? 1 : 'any')" :list="['depends_on_task_id', 'dependency_task_ids', 'task_id'].includes(name) ? id + '-tasks' : undefined" @input="change" /><datalist v-if="['depends_on_task_id', 'dependency_task_ids', 'task_id'].includes(name)" :id="id + '-tasks'"><option v-for="task in workspace.taskChoices" :key="String(task.id)" :value="String(task.id)">{{ task.title }}</option></datalist></template>
    <input v-else-if="part.format === 'date-time'" :id="id" type="datetime-local" :value="localTime" min="1000-01-01T00:00" max="9999-12-31T23:59" @input="change" />
    <textarea v-else-if="(part.maxLength ?? 0) > 500" :id="id" rows="3" :maxlength="part.maxLength" :value="String(modelValue ?? '')" @input="change"></textarea>
    <input v-else :id="id" :value="modelValue ?? ''" :maxlength="part.maxLength" @input="change" />
  </div>
  <p v-if="errors[path]" class="field-error" role="alert">{{ errors[path] }}</p>
</template>
