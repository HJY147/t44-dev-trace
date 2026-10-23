<script setup lang="ts">
import { asArray, asRow, label, safeLink } from '../contract'
import type { Json } from '../contract'
import { display } from '../workspace'
defineProps<{ value: Json; field?: string }>()
</script>

<template>
  <ol v-if="Array.isArray(value)" class="record-array"><li v-for="(item, index) in asArray(value)" :key="index"><RecordView :value="item" :field="field" /></li><li v-if="!value.length" class="muted">暂无记录</li></ol>
  <dl v-else-if="value && typeof value === 'object'" class="record-details"><template v-for="(item, key) in asRow(value)" :key="key"><div v-if="!['access_token', 'password', 'token_type'].includes(key)" class="record-detail"><dt>{{ label(key) }}</dt><dd><RecordView :value="item" :field="key" /></dd></div></template></dl>
  <a v-else-if="field === 'locator' && typeof value === 'string' && safeLink(value)" :href="safeLink(value)!" target="_blank" rel="noopener noreferrer">{{ value }} ↗</a>
  <span v-else>{{ display(value, field) }}</span>
</template>
