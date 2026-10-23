<script setup lang="ts">
import { computed } from 'vue'
import { ElButton, ElIcon, ElSkeleton } from 'element-plus'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/icon/style/css'
import 'element-plus/es/components/skeleton/style/css'
import { Connection, FolderOpened, Lock, RefreshRight, Warning } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  kind: 'unavailable' | 'empty' | 'loading' | 'error'
  title?: string
  description?: string
  httpStatus?: number
  refreshable?: boolean
}>(), { refreshable: false })

const emit = defineEmits<{ refresh: [] }>()
const isForbidden = computed(() => props.kind === 'error' && props.httpStatus === 403)
const isConflict = computed(() => props.kind === 'error' && props.httpStatus === 409)
const copy = computed(() => {
  if (isForbidden.value) return { title: '没有访问权限', description: '当前账号无法访问这项内容。请联系项目经理确认项目权限。', icon: Lock }
  if (isConflict.value) return { title: '页面信息已经变化', description: '本次操作未被接受。请刷新最新记录，核对后再决定下一步。', icon: RefreshRight }
  if (props.kind === 'error') return { title: '暂时无法加载', description: '请稍后刷新。若问题持续，请联系工作空间管理员。', icon: Warning }
  if (props.kind === 'empty') return { title: '暂无记录', description: '新的记录会显示在这里。', icon: FolderOpened }
  return { title: '等待连接工作空间', description: '连接后，这里将展示你有权访问的真实记录。', icon: Connection }
})
</script>

<template>
  <div v-if="kind === 'loading'" class="data-state data-state--loading" role="status" aria-live="polite" aria-busy="true">
    <span class="sr-only">正在加载记录</span>
    <ElSkeleton :rows="4" animated />
  </div>
  <div v-else class="data-state" :class="{ 'data-state--error': kind === 'error' }" :role="kind === 'error' ? 'alert' : 'status'" aria-live="polite">
    <div class="data-state__art" aria-hidden="true"><ElIcon :size="30"><component :is="copy.icon" /></ElIcon></div>
    <p class="data-state__title">{{ title ?? copy.title }}</p>
    <p class="data-state__description">{{ description ?? copy.description }}</p>
    <ElButton v-if="kind === 'error' && refreshable && !isForbidden" :icon="RefreshRight" @click="emit('refresh')">刷新记录</ElButton>
    <slot />
  </div>
</template>
