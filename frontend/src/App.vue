<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElButton, ElConfigProvider, ElDialog, ElDrawer, ElIcon } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { ArrowRight, Close, InfoFilled, Menu, User } from '@element-plus/icons-vue'
import 'element-plus/es/components/button/style/css'
import 'element-plus/es/components/dialog/style/css'
import 'element-plus/es/components/drawer/style/css'
import 'element-plus/es/components/icon/style/css'
import SidebarNavigation from './components/SidebarNavigation.vue'
import LoginView from './components/LoginView.vue'
import { logout, workspace } from './workspace'

const route = useRoute()
const mobileNavigation = ref(false)
const showAccessInfo = ref(false)
const currentTitle = computed(() => String(route.meta.title ?? '工作空间'))
watch(() => route.fullPath, () => { mobileNavigation.value = false })
async function signOut(): Promise<void> {
  try { await logout() } catch (cause) { workspace.notice = cause instanceof Error ? cause.message : '退出尚未完成，请重试。' }
}
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <a class="skip-link" href="#main-content">跳转到主要内容</a>
    <div class="app-shell" :inert="!workspace.user">
      <aside class="sidebar" aria-label="工作空间侧栏"><SidebarNavigation /></aside>
      <div class="app-main">
        <header class="topbar">
          <div class="topbar__left">
            <ElButton class="mobile-menu" circle :icon="Menu" aria-label="打开主导航" :aria-expanded="mobileNavigation" @click="mobileNavigation = true" />
            <span class="breadcrumb"><span class="breadcrumb__root">工作空间</span><ElIcon :size="12" aria-hidden="true"><ArrowRight /></ElIcon><span aria-current="page">{{ currentTitle }}</span></span>
          </div>
          <div class="topbar__right">
            <label class="project-picker"><span class="sr-only">当前项目</span><select v-model="workspace.projectId"><option :value="null">选择项目</option><option v-for="project in workspace.projects" :key="String(project.id)" :value="Number(project.id)">{{ project.name }}</option></select></label>
            <ElButton class="access-help" text :icon="InfoFilled" @click="showAccessInfo = true">访问说明</ElButton>
            <span class="topbar__divider" aria-hidden="true"></span>
            <span class="account"><span class="account__avatar" aria-hidden="true"><ElIcon><User /></ElIcon></span><span>{{ workspace.user?.display_name }}</span></span><ElButton text @click="signOut">退出</ElButton>
          </div>
        </header>
        <main id="main-content" class="workspace" tabindex="-1">
          <RouterView v-slot="{ Component }"><component :is="Component" :key="route.path" /></RouterView>
          <footer class="workspace-footer"><span>留痕 · 研发流程与交付记录</span><span>时间显示：北京时间</span></footer>
        </main>
      </div>
    </div>
    <ElDrawer v-model="mobileNavigation" class="mobile-navigation" direction="ltr" size="272px" :with-header="false" title="主导航" :close-on-click-modal="true" :close-on-press-escape="true">
      <ElButton class="drawer-close" circle :icon="Close" aria-label="关闭主导航" @click="mobileNavigation = false" />
      <SidebarNavigation @navigate="mobileNavigation = false" />
    </ElDrawer>
    <ElDialog v-model="showAccessInfo" title="工作空间访问说明" width="min(460px, calc(100vw - 32px))">
      <p class="access-description">当前工作空间仅展示你参与项目的任务、评审与交付记录。记录中的时间统一显示为北京时间。</p>
      <p class="access-description">涉及任务推进、发布和回滚的操作，需要相应项目权限与完整依据。</p>
      <template #footer><ElButton type="primary" @click="showAccessInfo = false">知道了</ElButton></template>
    </ElDialog>
    <LoginView v-if="!workspace.user" />
  </ElConfigProvider>
</template>
