import {
  Bell, Calendar, Collection, DocumentChecked, Files, Grid, List,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

export type WorkspacePage = 'overview' | 'projects' | 'tasks' | 'schedule' | 'reviews' | 'notifications' | 'audit'

export const navigation: { key: WorkspacePage; path: string; label: string; icon: Component; group: string }[] = [
  { key: 'overview', path: '/', label: '工作台', icon: Grid, group: '工作空间' },
  { key: 'projects', path: '/projects', label: '项目空间', icon: Files, group: '工作空间' },
  { key: 'tasks', path: '/tasks', label: '交付任务', icon: List, group: '研发流程' },
  { key: 'schedule', path: '/schedule', label: '迭代排期', icon: Calendar, group: '研发流程' },
  { key: 'reviews', path: '/reviews', label: '评审与发布', icon: DocumentChecked, group: '研发流程' },
  { key: 'notifications', path: '/notifications', label: '通知中心', icon: Bell, group: '记录与协作' },
  { key: 'audit', path: '/audit', label: '审计记录', icon: Collection, group: '记录与协作' },
]

export const navigationGroups = [...new Set(navigation.map((item) => item.group))]
