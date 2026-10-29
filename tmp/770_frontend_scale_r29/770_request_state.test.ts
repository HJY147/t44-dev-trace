import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import TaskDrawer from '../../frontend/src/components/TaskDrawer.vue'
import WorkspaceView from '../../frontend/src/views/WorkspaceView.vue'
import { workspace } from '../../frontend/src/workspace'
import { fixtureFetch, page, seed, task } from '../frontend/981_fixtures'

const global = { stubs: { teleport: true } }
const mounted: ReturnType<typeof mount>[] = []
const settle = async () => { await flushPromises(); await nextTick(); await flushPromises() }
const response = (data: unknown, status = 200) => new Response(JSON.stringify(status === 200 ? { data, meta: { replayed: false } } : data), { status })
const button = (wrapper: ReturnType<typeof mount>, text: string) => wrapper.findAll('button').find(node => node.text() === text)!

beforeEach(seed)
afterEach(() => { mounted.splice(0).forEach(wrapper => wrapper.unmount()); vi.unstubAllGlobals(); document.body.innerHTML = '' })

describe('shared request state regression', () => {
  it('keeps the latest task visible when an older parent-triggered refresh fails', async () => {
    const { fetcher } = fixtureFetch()
    let release!: (value: Response) => void
    fetcher.mockImplementationOnce(() => new Promise<Response>(resolve => { release = resolve }))
    const wrapper = mount(TaskDrawer, { props: { projectId: 1, taskId: 1, revision: 0 }, global })
    mounted.push(wrapper); await settle()
    await wrapper.setProps({ revision: 1 }); await settle()
    expect(wrapper.text()).toContain(String(task.title))
    release(response({ message: '迟到旧读取失败' }, 503)); await settle()
    expect(wrapper.text()).toContain(String(task.title))
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('[aria-busy="true"]').exists()).toBe(false)
  })

  it('does not start a stale task-history read after a newer refresh has completed', async () => {
    const { fetcher, calls } = fixtureFetch()
    const wrapper = mount(TaskDrawer, { props: { projectId: 1, taskId: 1, revision: 0 }, global })
    mounted.push(wrapper); await settle()
    let release!: (value: Response) => void
    fetcher.mockImplementationOnce(() => new Promise<Response>(resolve => { release = resolve }))
    await button(wrapper, '前置依赖').trigger('click'); await settle()
    await wrapper.setProps({ revision: 1 }); await settle()
    const historyReads = calls.filter(call => call.path.endsWith('/dependencies')).length
    expect(historyReads).toBe(1)
    release(response({ ...task, title: '迟到旧任务标题' })); await settle()
    expect(calls.filter(call => call.path.endsWith('/dependencies'))).toHaveLength(historyReads)
    expect(wrapper.text()).not.toContain('迟到旧任务标题')
    expect(wrapper.findAll('.business-card')).toHaveLength(1)
  })

  it('ignores an older workspace error and still presents a current error with working refresh', async () => {
    const { fetcher } = fixtureFetch()
    const base = fetcher.getMockImplementation()!
    const wrapper = mount(WorkspaceView, { props: { page: 'tasks' }, global })
    mounted.push(wrapper); await settle()
    let release!: (value: Response) => void
    let delayNext = true
    fetcher.mockImplementation((url, init) => {
      if (String(url).split('?')[0] === '/api/v1/projects/1/tasks' && delayNext) {
        delayNext = false
        return new Promise<Response>(resolve => { release = resolve })
      }
      return base(url, init)
    })
    await button(wrapper, '刷新记录').trigger('click'); await settle()
    expect(release).toBeTypeOf('function')
    workspace.projectId = 2; await settle()
    workspace.projectId = 1; await settle()
    release(response({ message: '迟到旧页面错误' }, 503)); await settle()
    expect(wrapper.text()).toContain(String(task.title))
    expect(wrapper.text()).not.toContain('迟到旧页面错误')
    fetcher.mockResolvedValueOnce(response({ message: '当前读取失败' }, 503))
    await button(wrapper, '刷新记录').trigger('click'); await settle()
    expect(wrapper.get('[role="alert"]').text()).toContain('当前读取失败')
    expect(wrapper.findAll('.business-card')).toHaveLength(0)
    await button(wrapper, '刷新记录').trigger('click'); await settle()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.findAll('.business-card')).toHaveLength(Number(page([task]).total))
  })
})
