<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElButton, ElIcon, ElInput, ElOption, ElSelect, ElTabPane, ElTable, ElTableColumn, ElTabs } from 'element-plus'
import { ArrowRight, Bell, Calendar, CircleCheck, Clock, DocumentChecked, Files, Link, List, Plus, Search } from '@element-plus/icons-vue'
import 'element-plus/es/components/input/style/css'
import 'element-plus/es/components/select/style/css'
import 'element-plus/es/components/option/style/css'
import 'element-plus/es/components/table/style/css'
import 'element-plus/es/components/table-column/style/css'
import 'element-plus/es/components/tabs/style/css'
import 'element-plus/es/components/tab-pane/style/css'
import type { WorkspacePage } from '../navigation'
import DataState from '../components/DataState.vue'
import PageHeading from '../components/PageHeading.vue'

const props = defineProps<{ page: WorkspacePage }>()
const activeTab = ref('first')
const pageDetails = {
  overview: { title: '工作台', description: '聚焦正在推进的交付，让进度、证据与每一次决定保持连贯。', section: '我的交付任务', empty: '你的交付任务将在这里汇集', detail: '连接工作空间后，查看分配给你的任务与下一步安排。' },
  projects: { title: '项目空间', description: '在一个地方组织成员、迭代与交付，保留项目协作的完整脉络。', section: '我参与的项目', empty: '在这里找到你参与的项目', detail: '连接工作空间后，选择项目以查看成员、计划和交付记录。' },
  tasks: { title: '交付任务', description: '沿着交付流程查看任务进展，记录阻塞、解除依据与流转历史。', section: '全部交付任务', empty: '交付从一条清晰的任务开始', detail: '连接工作空间并选择项目后，查看真实任务与流转记录。' },
  schedule: { title: '迭代排期', description: '把计划、依赖和人力安排放在一起，给每次调整留下依据。', section: '迭代计划', empty: '为下一次交付留出清晰的计划', detail: '连接工作空间并选择项目后，查看迭代、依赖与排期差异。' },
  reviews: { title: '评审与发布', description: '将代码证据、上线风险与回滚预案串联到每次交付决定。', section: '评审记录', empty: '每一次评审，都应有据可查', detail: '连接工作空间并选择项目后，查看评审证据和上线评估。' },
  notifications: { title: '通知中心', description: '集中查看与你有关的交付提醒，分别记录阅读与处理进展。', section: '我的通知', empty: '让需要关注的事及时被看见', detail: '连接工作空间后，查看发给你的通知与站内待办。' },
  audit: { title: '审计记录', description: '按时间追溯项目内的操作与决定，还原每次变更的来龙去脉。', section: '项目操作记录', empty: '项目操作将在这里留下轨迹', detail: '连接工作空间并选择项目后，查看可访问范围内的审计记录。' },
} as const
const detail = computed(() => pageDetails[props.page])
const rows: never[] = []
const columns = computed(() => {
  if (props.page === 'projects') return ['项目名称', '项目说明', '创建时间']
  if (props.page === 'schedule') return ['迭代名称', '计划时间', '缓冲安排', '人力产能']
  if (props.page === 'reviews') return activeTab.value === 'first' ? ['交付任务', '评审版本', '证据与判定', '提交时间'] : ['交付任务', '评估版本', '评审情况', '决定记录']
  if (props.page === 'notifications') return ['提醒内容', '所属项目', '提醒级别', '阅读与处理', '通知时间']
  if (props.page === 'audit') return ['操作内容', '操作者', '发生时间', '结果', '记录编号']
  return ['交付任务', '所属项目', '负责人', '计划交付', '当前状态']
})
const metrics = [
  { label: '参与项目', icon: Files, hint: '保持团队协作的上下文', tone: 'blue' },
  { label: '进行中交付', icon: List, hint: '关注任务与依赖进展', tone: 'cyan' },
  { label: '评审与发布', icon: DocumentChecked, hint: '证据与决策逐项留痕', tone: 'violet' },
  { label: '待处理提醒', icon: Bell, hint: '及时回应需要关注的事', tone: 'amber' },
]
const shortcuts = [
  { title: '整理项目与成员', description: '先让协作范围与责任归位', path: '/projects', icon: Files },
  { title: '安排下一次交付', description: '明确计划、缓冲与依赖', path: '/schedule', icon: Calendar },
  { title: '核对评审与预案', description: '把证据留在决定之前', path: '/reviews', icon: DocumentChecked },
]
</script>

<template>
  <PageHeading :title="detail.title" :description="detail.description" eyebrow="研发交付 / WORKSPACE">
    <span class="connection-badge"><span aria-hidden="true"></span>等待连接</span>
  </PageHeading>

  <div class="connection-notice" role="status">
    <span class="connection-notice__icon" aria-hidden="true"><ElIcon :size="18"><Link /></ElIcon></span>
    <div><strong>工作空间记录暂不可用</strong><span>连接后同步你有权访问的项目与记录。当前不显示统计数量。</span></div>
  </div>

  <section v-if="page === 'overview'" class="metric-grid" aria-label="工作空间概览">
    <article v-for="metric in metrics" :key="metric.label" class="metric-card">
      <div class="metric-card__top"><span>{{ metric.label }}</span><span class="metric-card__icon" :class="`tone-${metric.tone}`" aria-hidden="true"><ElIcon :size="19"><component :is="metric.icon" /></ElIcon></span></div>
      <p class="metric-card__value" aria-label="尚无可用统计">—</p><p class="metric-card__hint">{{ metric.hint }}</p>
    </article>
  </section>

  <div class="content-grid" :class="{ 'content-grid--single': !['overview', 'schedule', 'reviews'].includes(page) }">
    <section class="surface records-panel" :aria-label="detail.section">
      <div class="panel-heading"><div><h2>{{ detail.section }}</h2><p>{{ page === 'overview' ? '从这里查看交付进度与待办' : '项目记录将在连接后显示' }}</p></div>
        <RouterLink v-if="page === 'overview'" to="/tasks" class="text-link">查看全部<ElIcon aria-hidden="true"><ArrowRight /></ElIcon></RouterLink>
        <ElButton v-else-if="page === 'projects' || page === 'tasks' || page === 'schedule'" :icon="Plus" disabled :aria-label="`${page === 'projects' ? '新建项目' : page === 'tasks' ? '登记任务' : '新建迭代'}，连接后可用`">{{ page === 'projects' ? '新建项目' : page === 'tasks' ? '登记任务' : '新建迭代' }}</ElButton>
      </div>
      <ElTabs v-if="page === 'reviews' || page === 'notifications'" v-model="activeTab" class="record-tabs" :aria-label="page === 'reviews' ? '评审类型' : '通知范围'">
        <ElTabPane :label="page === 'reviews' ? '代码评审' : '待处理'" name="first" />
        <ElTabPane :label="page === 'reviews' ? '上线评估与决定' : '全部通知'" name="second" />
      </ElTabs>
      <div class="filter-bar">
        <div class="filter-field"><label :for="`search-${page}`">{{ page === 'audit' ? '搜索操作记录' : page === 'notifications' ? '搜索通知' : '搜索名称或关键词' }}</label><ElInput :id="`search-${page}`" :prefix-icon="Search" placeholder="连接后可搜索" disabled /></div>
        <div v-if="page !== 'projects'" class="filter-field filter-field--select"><label :for="`scope-${page}`">{{ page === 'overview' || page === 'tasks' ? '任务状态' : '项目范围' }}</label><ElSelect :id="`scope-${page}`" :model-value="''" placeholder="连接后可筛选" disabled><ElOption value="" label="连接后可筛选" /></ElSelect></div>
      </div>
      <div class="records-table" tabindex="0" role="region" :aria-label="`${detail.section}表格，可横向滚动`">
        <ElTable :data="rows" style="width: 100%" :aria-label="detail.section" :empty-text="detail.empty">
          <ElTableColumn v-for="(column, index) in columns" :key="column" :label="column" :min-width="index === 0 ? 180 : 120" />
          <template #empty><DataState kind="unavailable" :title="detail.empty" :description="detail.detail" /></template>
        </ElTable>
      </div>
      <div class="panel-footnote"><span class="neutral-dot" aria-hidden="true"></span>记录尚未加载<span class="panel-footnote__right">{{ page === 'audit' ? '仅展示有权访问的项目记录' : '真实进展以工作空间记录为准' }}</span></div>
    </section>

    <aside v-if="page === 'overview'" class="context-column" aria-label="工作指引">
      <section class="surface quick-start"><div class="panel-heading"><h2>从这里开始</h2><span class="section-index">01 — 03</span></div>
        <RouterLink v-for="(shortcut, index) in shortcuts" :key="shortcut.path" :to="shortcut.path" class="shortcut"><span class="shortcut__number">0{{ index + 1 }}</span><div><strong>{{ shortcut.title }}</strong><p>{{ shortcut.description }}</p></div><ElIcon class="shortcut__arrow" aria-hidden="true"><ArrowRight /></ElIcon></RouterLink>
      </section>
      <section class="attention-card"><span class="attention-card__eyebrow"><ElIcon aria-hidden="true"><CircleCheck /></ElIcon>交付中的关键时刻</span><h2>让依据走在决定前面</h2><p>阻塞记清原因，变更保留差异，评审附上证据。每次推进，都有完整脉络可循。</p><RouterLink to="/audit" class="text-link">查看项目记录<ElIcon aria-hidden="true"><ArrowRight /></ElIcon></RouterLink></section>
    </aside>
    <aside v-if="page === 'schedule' || page === 'reviews'" class="context-column" :aria-label="page === 'schedule' ? '排期说明' : '评审说明'">
      <section class="surface context-card"><span class="context-card__icon" aria-hidden="true"><ElIcon :size="22"><component :is="page === 'schedule' ? Clock : DocumentChecked" /></ElIcon></span><h2>{{ page === 'schedule' ? '为变化留出余量' : '证据与决定放在一起' }}</h2><p>{{ page === 'schedule' ? '查看计划时间、人力安排与缓冲。每次改期保留调整前后差异与依据。' : '评审证据、风险应对与回滚预案关联具体版本，发布和回滚保留拍板依据。' }}</p><div class="context-divider"></div><p class="context-card__note">{{ page === 'schedule' ? '依赖是否满足、任务能否开始，以提交后的校验结果为准。' : '查看记录不等于获得批准。相关操作需由有权限的项目成员作出。' }}</p></section>
    </aside>
  </div>
</template>
