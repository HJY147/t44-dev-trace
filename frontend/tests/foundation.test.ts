import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DataState from '../src/components/DataState.vue'

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
