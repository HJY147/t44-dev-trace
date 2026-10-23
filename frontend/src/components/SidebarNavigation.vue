<script setup lang="ts">
import { ElIcon } from 'element-plus'
import { ArrowRight, Connection } from '@element-plus/icons-vue'
import { navigation, navigationGroups } from '../navigation'
import { workspace } from '../workspace'

defineEmits<{ navigate: [] }>()
</script>

<template>
  <RouterLink class="brand" to="/" aria-label="留痕，返回工作台" @click="$emit('navigate')">
    <img src="/favicon.svg" width="38" height="38" alt="" />
    <span><strong>留痕</strong><small>研发交付工作空间</small></span>
  </RouterLink>
  <RouterLink class="project-switch" to="/projects" @click="$emit('navigate')">
    <span class="project-switch__avatar" aria-hidden="true">项</span>
    <span><strong>{{ workspace.project.name ?? '选择项目' }}</strong><small>{{ workspace.projectId ? '当前项目工作空间' : '从项目空间开始' }}</small></span>
    <ElIcon aria-hidden="true"><ArrowRight /></ElIcon>
  </RouterLink>
  <nav aria-label="主导航" class="navigation">
    <div v-for="group in navigationGroups" :key="group" class="navigation__group">
      <p class="navigation__label">{{ group }}</p>
      <RouterLink v-for="item in navigation.filter((entry) => entry.group === group)" :key="item.key" :to="item.path" :exact-active-class="'navigation__link--active'" class="navigation__link" @click="$emit('navigate')">
        <ElIcon :size="19" aria-hidden="true"><component :is="item.icon" /></ElIcon>
        <span>{{ item.label }}</span>
      </RouterLink>
    </div>
  </nav>
  <div class="sidebar-footer">
    <span class="sidebar-footer__icon" aria-hidden="true"><ElIcon><Connection /></ElIcon></span>
    <div><strong>记录从这里开始</strong><p>让每次交付有据可循</p></div>
  </div>
</template>
