import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import DataState from '../src/components/DataState.vue'
import App from '../src/App.vue'
import WorkspaceView from '../src/views/WorkspaceView.vue'
import { navigation } from '../src/navigation'

afterEach(() => { document.body.innerHTML = '' })

describe('resource feedback', () => {
  it('keeps forbidden access distinct from a refreshable failure', () => {
    const wrapper = mount(DataState, { props: { kind: 'error', httpStatus: 403, refreshable: true } })
    expect(wrapper.attributes('role')).toBe('alert')
    expect(wrapper.text()).toContain('没有访问权限')
    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.emitted()).toEqual({})
    wrapper.unmount()
  })

  it('refreshes records after a conflict without emitting a write or retry action', async () => {
    const wrapper = mount(DataState, { props: { kind: 'error', httpStatus: 409, refreshable: true } })
    expect(wrapper.text()).toContain('本次操作未被接受')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)
    expect(wrapper.emitted('retry')).toBeUndefined()
    expect(wrapper.emitted('submit')).toBeUndefined()
    wrapper.unmount()
  })

  it('announces loading without treating it as an empty successful response', () => {
    const wrapper = mount(DataState, { props: { kind: 'loading' } })
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.text()).toContain('正在加载记录')
    expect(wrapper.text()).not.toContain('暂无记录')
    wrapper.unmount()
  })

  it('distinguishes an unconnected workspace from an empty result', () => {
    const unavailable = mount(DataState, { props: { kind: 'unavailable' } })
    const empty = mount(DataState, { props: { kind: 'empty' } })
    expect(unavailable.text()).toContain('等待连接工作空间')
    expect(empty.text()).toContain('暂无记录')
    expect(unavailable.find('button').exists()).toBe(false)
    unavailable.unmount()
    empty.unmount()
  })
})

describe('workspace navigation', () => {
  it('navigates among actual pages while leaving unavailable write controls disabled', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: navigation.map((item) => ({ path: item.path, component: WorkspaceView, props: { page: item.key }, meta: { title: item.label } })),
    })
    await router.push('/tasks')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] }, attachTo: document.body })
    expect(wrapper.get('h1').text()).toBe('交付任务')
    expect(wrapper.get('button[aria-label="登记任务，连接后可用"]').attributes('disabled')).toBeDefined()
    await wrapper.get('a[href="/reviews"].navigation__link').trigger('click')
    await router.isReady()
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(wrapper.get('h1').text()).toBe('评审与发布')
    await wrapper.get('a[href="/notifications"].navigation__link').trigger('click')
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(wrapper.get('h1').text()).toBe('通知中心')
    expect(wrapper.findAll('tbody tr')).toHaveLength(0)
    expect(wrapper.text()).not.toContain('保存成功')
    wrapper.unmount()
  })
})
