import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import App from '../../frontend/src/App.vue'
import WorkspaceView from '../../frontend/src/views/WorkspaceView.vue'
import { api, request } from '../../frontend/src/api'
import { context, logout, workspace } from '../../frontend/src/workspace'
import { envelope, fixtureFetch, page, project, seed, user } from './981_fixtures'
const settle = async () => { await flushPromises(); await nextTick(); await flushPromises() }
const mounted: ReturnType<typeof mount>[] = []
const global = { stubs: { teleport: true } }
beforeEach(seed)
afterEach(() => { mounted.splice(0).forEach(wrapper => wrapper.unmount()); vi.unstubAllGlobals(); document.body.innerHTML = '' })
const response = (data: unknown, status = 200) => new Response(JSON.stringify(status === 200 ? envelope(data as never) : data), { status })

describe('reviewer targeted session lifecycle probes on exact 3c160c5', () => {
  it('keeps the latest of concurrent same-project context reads', async () => {
    const { fetcher } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    let release!: (value: Response) => void
    fetcher.mockImplementationOnce(() => new Promise<Response>(resolve => { release = resolve }))
    const old = context(); await context()
    const latest = JSON.stringify(workspace.project)
    release(response({ ...project, name: '迟到旧上下文' })); await old
    expect(JSON.stringify(workspace.project)).toBe(latest)
    expect(fetcher.getMockImplementation()).toBe(base)
  })
  it('preserves a newly logged-in identity when an older logout success arrives after current-session 401', async () => {
    const { fetcher } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    let release!: (value: Response) => void
    fetcher.mockImplementation((url, init) => String(url).endsWith('/auth/logout') ? new Promise<Response>(resolve => { release = resolve }) : base(url, init))
    const pending = logout(); const rejected = expect(pending).rejects.toMatchObject({ detail: { code: 'SESSION_CHANGED' } })
    fetcher.mockResolvedValueOnce(response({ message: '会话已失效' }, 401))
    await expect(request('getMe')).rejects.toMatchObject({ status: 401 })
    api.token = 'new-synthetic-session'; workspace.user = { ...user, id: 2 }
    release(response({ acknowledged: true })); await rejected
    expect(api.token).toBe('new-synthetic-session'); expect(workspace.user?.id).toBe(2)
  })
  it('does not let an unmounted old form error refresh and erase a new login context', async () => {
    const freshProject = { ...project, id: 2, name: '新身份项目' }
    const { fetcher } = fixtureFetch({ '/api/v1/projects': page([freshProject]), '/api/v1/projects/2': freshProject })
    const base = fetcher.getMockImplementation()!
    let failOld!: (value: Response) => void; let lateOldFailure = false
    const orphanReads: string[] = []
    fetcher.mockImplementation((url, init) => {
      const path = String(url).split('?')[0]!
      if (path === '/api/v1/projects' && init?.method === 'POST') return new Promise<Response>(resolve => { failOld = resolve })
      if (path.endsWith('/auth/login')) return Promise.resolve(response({ access_token: 'second-synthetic-session', user: { ...user, id: 2 } }))
      if (path.endsWith('/auth/me') && api.token === 'second-synthetic-session') return Promise.resolve(response({ ...user, id: 2 }))
      if (lateOldFailure && init?.method === 'GET' && path.startsWith('/api/v1/projects/2')) {
        orphanReads.push(path); return Promise.resolve(response({ message: '当前读取暂不可用' }, 503))
      }
      return base(url, init)
    })
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/projects', component: WorkspaceView, props: { page: 'projects' } }] })
    await router.push('/projects'); await router.isReady()
    const app = mount(App, { global: { ...global, plugins: [router] }, attachTo: document.body }); mounted.push(app); await settle()
    const click = async (text: string) => { await app.findAll('button').find(node => node.text() === text)!.trigger('click'); await settle() }
    await click('创建项目'); await app.get('#field-name').setValue('旧身份待创建项目'); await app.get('#field-description').setValue('受控夹具')
    await app.get('.operation-form').trigger('submit'); await settle(); expect(failOld).toBeTypeOf('function')
    await click('退出'); expect(app.find('.operation-form').exists()).toBe(false)
    await app.get('#login-username').setValue('second-fixture-user'); await app.get('#login-password').setValue('synthetic-password')
    await app.get('form').trigger('submit'); await settle()
    expect(workspace.user?.id).toBe(2); expect(workspace.project.name).toBe('新身份项目')
    lateOldFailure = true; failOld(response({ message: '旧身份无创建权限' }, 403)); await settle()
    console.log('REVIEWER_ORPHAN_FORM_TRACE', JSON.stringify({ orphanReads, tokenUnchanged: api.token === 'second-synthetic-session', currentUser: workspace.user?.id, projectAfterOldFailure: workspace.project }))
    expect(workspace.project.name).toBe('新身份项目')
    expect(orphanReads).toEqual([])
  })
})
