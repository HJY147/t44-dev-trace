import { createRouter, createWebHistory } from 'vue-router'
import { nextTick } from 'vue'
import { navigation } from './navigation'
import WorkspaceView from './views/WorkspaceView.vue'
import NotFoundView from './views/NotFoundView.vue'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...navigation.map((item) => ({
      path: item.path,
      name: item.key,
      component: WorkspaceView,
      props: { page: item.key },
      meta: { title: item.label },
    })),
    { path: '/:pathMatch(.*)*', component: NotFoundView, meta: { title: '页面不存在' } },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach(async (to, from) => {
  document.title = `${String(to.meta.title ?? '工作空间')} · 留痕`
  if (from.matched.length) {
    await nextTick()
    document.querySelector<HTMLElement>('#page-heading')?.focus()
  }
})
