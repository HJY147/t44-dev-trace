<script setup lang="ts">
import { asRow, beijing } from '../contract'
import type { Row } from '../contract'
import { display } from '../workspace'
import RecordView from './RecordView.vue'
withDefaults(defineProps<{ rows: Row[]; total: number; page: number; pageSize?: number; clickable?: boolean }>(), { pageSize: 20 })
defineEmits<{ page: [value: number]; select: [row: Row] }>()
</script>

<template>
  <div class="business-records">
    <article v-for="(row, index) in rows" :key="String(row.id ?? asRow(row.user).id ?? index)" class="business-card">
      <div class="business-card__heading"><h3><button v-if="clickable" class="text-button" @click="$emit('select', row)">{{ row.title ?? row.name ?? '任务 #' + row.id }}</button><span v-else>{{ row.title ?? row.name ?? asRow(row.user).display_name ?? (row.operation_id ? display(row.operation_id) : '记录 #' + (row.id ?? index + 1)) }}</span></h3><span v-if="row.state !== undefined" class="state-pill">{{ display(row.state, 'state') }}</span><span v-else-if="row.status !== undefined" class="state-pill">{{ display(row.status, 'status') }}</span></div>
      <p v-if="row.description || row.message" class="record-summary">{{ row.description ?? row.message }}</p>
      <div class="record-meta"><span v-if="row.id">编号 {{ row.id }}</span><span v-if="row.version">版本 {{ row.version }}</span><span v-if="row.owner_id">负责人 {{ display(row.owner_id, 'owner_id') }}</span><span v-if="asRow(row.plan).planned_end">计划交付 {{ beijing(String(asRow(row.plan).planned_end)) }}</span><span v-if="row.created_at">{{ beijing(String(row.created_at)) }}</span><span v-if="row.read_at !== undefined">{{ row.read_at ? '已读' : '未读' }} · {{ row.handled_at ? '已处理' : '未处理' }}</span><span v-if="row.fallback" class="warm-text">降级站内待办</span></div>
      <slot :row="row" />
      <details><summary>查看完整记录</summary><RecordView :value="row" /></details>
    </article>
    <div class="business-pagination"><span>共 {{ total }} 条 · 第 {{ page }} 页</span><button class="secondary-button" :disabled="page <= 1" @click="$emit('page', page - 1)">上一页</button><button class="secondary-button" :disabled="page * pageSize >= total" @click="$emit('page', page + 1)">下一页</button></div>
  </div>
</template>
