<script setup lang="ts">
import { computed } from 'vue'
import { asArray, asRow, label, safeLink } from '../contract'
import type { Json } from '../contract'
import { display } from '../workspace'
import { auditReason } from '../audit'
const props = defineProps<{ value: Json; field?: string }>()
const reason = computed(() => auditReason(asRow(props.value)))
</script>

<template>
  <ol v-if="Array.isArray(value)" class="record-array"><li v-for="(item, index) in asArray(value)" :key="index"><RecordView :value="item" :field="field" /></li><li v-if="!value.length" class="muted">暂无记录</li></ol>
  <dl v-else-if="field === 'after' && asRow(value).field === 'reason'" class="record-details"><div class="record-detail" data-raw-plan-reason><dt>原始理由条目（未核对）</dt><dd>{{ typeof asRow(value).value === 'string' ? asRow(value).value : JSON.stringify(asRow(value).value) }}</dd></div></dl>
  <dl v-else-if="value && typeof value === 'object'" class="record-details">
    <div v-if="reason?.text !== undefined" class="record-detail" data-plan-reason><dt>{{ label('reason') }}</dt><dd>{{ reason.text }}</dd></div>
    <div v-if="reason?.missing" class="record-detail"><dt>理由核对</dt><dd data-plan-reason-missing>此历史记录未提供可核对的变更理由</dd></div>
    <template v-for="(item, key) in asRow(value)" :key="key"><div v-if="!['access_token', 'password', 'token_type'].includes(key)" class="record-detail"><dt>{{ label(key) }}</dt><dd><RecordView :value="key === 'after' && reason?.text !== undefined ? asArray(item).filter(entry => asRow(entry).field !== 'reason') : item" :field="key" /></dd></div></template>
  </dl>
  <a v-else-if="field === 'locator' && typeof value === 'string' && safeLink(value)" :href="safeLink(value)!" target="_blank" rel="noopener noreferrer">{{ value }} ↗</a>
  <span v-else>{{ display(value, field) }}</span>
</template>
