import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { nextTick } from 'vue'
import App from '../../frontend/src/App.vue'
import FieldEditor from '../../frontend/src/components/FieldEditor.vue'
import LoginView from '../../frontend/src/components/LoginView.vue'
import OperationForm from '../../frontend/src/components/OperationForm.vue'
import RecordList from '../../frontend/src/components/RecordList.vue'
import RecordView from '../../frontend/src/components/RecordView.vue'
import TaskDrawer from '../../frontend/src/components/TaskDrawer.vue'
import NotFoundView from '../../frontend/src/views/NotFoundView.vue'
import WorkspaceView from '../../frontend/src/views/WorkspaceView.vue'
import { navigation } from '../../frontend/src/navigation'
import { asRow, schemas } from '../../frontend/src/contract'
import type { Schema } from '../../frontend/src/contract'
import { formSchemas, presets } from '../../frontend/src/forms'
import { workspace } from '../../frontend/src/workspace'
import { api } from '../../frontend/src/api'
import { evidence, fixtureFetch, iteration, member, notification, page, seed, task, user } from './981_fixtures'
const global = { stubs: { teleport: true } }
const settle = async () => { await flushPromises(); await nextTick(); await flushPromises() }
const button = (wrapper: ReturnType<typeof mount>, text: string) => wrapper.findAll('button').find((node) => node.text() === text)!
beforeEach(() => { seed(); fixtureFetch() })
afterEach(() => { vi.unstubAllGlobals(); document.body.innerHTML = '' })

describe('typed editor interactions', () => {
  it('emits boolean, integer, date, text, enum and array changes as proper JSON values', async () => {
    const schema: Schema = { type: 'object', required: ['approved'], properties: { approved: { type: 'boolean' }, count: { type: 'integer' }, planned_start: { $ref: '#/components/schemas/UtcTime' }, description: { type: 'string', maxLength: 2000 }, owner_id: { type: 'integer' }, roles: { type: 'array', items: { type: 'integer' }, maxItems: 3 }, dependency_task_ids: { type: 'array', items: { type: 'integer' }, maxItems: 5 } } }
    const wrapper = mount(FieldEditor, { props: { schema, modelValue: { approved: false, count: 1, planned_start: '', description: '', owner_id: null, roles: [], dependency_task_ids: [1] }, 'onUpdate:modelValue': (value) => wrapper.setProps({ modelValue: value }) }, global })
    await wrapper.get('#field-approved').setValue(true)
    expect(asRow(wrapper.props('modelValue')).approved).toBe(true)
    await wrapper.get('#field-count').setValue(3); expect(asRow(wrapper.props('modelValue')).count).toBe(3)
    await wrapper.get('#field-planned_start').setValue('2026-10-23T12:30'); expect(asRow(wrapper.props('modelValue')).planned_start).toBe('2026-10-23T04:30:00.000Z')
    await wrapper.get('#field-description').setValue('中文说明'); expect(asRow(wrapper.props('modelValue')).description).toBe('中文说明')
    await wrapper.get('#field-owner_id').setValue('1'); expect(asRow(wrapper.props('modelValue')).owner_id).toBe(1)
    await button(wrapper, '添加项目角色').trigger('click'); await wrapper.get('#field-roles-0').setValue('2')
    expect(asRow(wrapper.props('modelValue')).roles).toEqual([2])
    await wrapper.findAll('button').find((node) => node.text() === '移除这一项')!.trigger('click')
    expect(asRow(wrapper.props('modelValue')).roles).toEqual([])
    await wrapper.get('#field-dependency_task_ids-0').setValue(2); expect(asRow(wrapper.props('modelValue')).dependency_task_ids).toEqual([2])
    wrapper.unmount()
  })
  it('shows server-template section names, safe evidence links, and human-readable record values', () => {
    const editor = mount(FieldEditor, { props: { schema: schemas.ReviewCreate!, modelValue: presets('createTaskReview', {}, task) }, global })
    expect(editor.text()).toContain('审核对象与基线'); expect(editor.text()).toContain('八段式评审记录'); editor.unmount()
    const record = mount(RecordView, { props: { value: { evidence: [evidence, { kind: 3, locator: 'javascript:alert(1)', description: '<img onerror=alert(1)>' }], active: true, before: [], password: 'never-render', access_token: 'never-render' } } })
    expect(record.findAll('a')).toHaveLength(1); expect(record.get('a').attributes('rel')).toBe('noopener noreferrer'); expect(record.text()).not.toContain('never-render'); expect(record.find('img').exists()).toBe(false); record.unmount()
  })
})
describe('operation forms', () => {
  it('submits a filled blocking form with optional document revision left blank', async () => {
    const { calls } = fixtureFetch()
    const wrapper = mount(OperationForm, { props: { operation: 'transitionTask', schemaName: 'BlockTransition', params: { project_id: 1, task_id: 1 }, preset: { expected_version: 1, action: 2 }, refresh: async () => {}, saved: async () => {} }, global })
    await settle(); await wrapper.get('#field-reason').setValue('模块测试阻塞原因'); await wrapper.get('#field-responsibility_stage').setValue('1')
    await wrapper.get('#field-evidence-0-kind').setValue('2'); await wrapper.get('#field-evidence-0-locator').setValue('agents/frontend/application.test.ts'); await wrapper.get('#field-evidence-0-description').setValue('真实测试脚本')
    await wrapper.get('form').trigger('submit'); await settle(); expect(calls.find((call) => call.method === 'POST')?.body.evidence).toMatchObject([{ kind: 2, revision: null }]); expect(wrapper.emitted('close')).toHaveLength(1); wrapper.unmount()
  })
  it('keeps a draft through 409, refreshes, explicitly adopts version, then confirms the authoritative result', async () => {
    const { fetcher, calls } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    let first = true
    fetcher.mockImplementation(async (url, init) => {
      if (String(url).endsWith('/projects/1/tasks/1/transitions') && first) { first = false; return new Response(JSON.stringify({ message: '已有新版本', code: 'VERSION_CONFLICT', current_version: 2, request_id: 'fixture-conflict', violations: [] }), { status: 409 }) }
      return base(url, init)
    })
    const refresh = vi.fn().mockResolvedValue(undefined), saved = vi.fn().mockResolvedValue(undefined)
    const wrapper = mount(OperationForm, { props: { operation: 'transitionTask', schemaName: 'StartTransition', params: { project_id: 1, task_id: 1 }, preset: { expected_version: 1, action: 1 }, refresh, saved }, global })
    await settle(); await wrapper.get('form').trigger('submit'); await settle()
    expect(refresh).toHaveBeenCalledOnce(); expect(wrapper.get('#field-expected_version').element).toHaveProperty('value', '1'); expect(wrapper.text()).toContain('已有新版本')
    await button(wrapper, '采用最新版本 2，保留其余内容').trigger('click'); await wrapper.get('form').trigger('submit'); await settle()
    expect(saved).toHaveBeenCalledOnce(); expect(wrapper.emitted('close')).toHaveLength(1); expect(calls.some((call) => call.body.expected_version === 2)).toBe(true); wrapper.unmount()
  })
  it('retains the same write key and body on uncertain retry and displays 422 field errors without closing', async () => {
    const fetcher = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(new Response(JSON.stringify({ message: '名称不合要求', code: 'PARAMETER_INVALID', violations: [{ path: '/name', message: '请重新填写名称' }] }), { status: 422 }))
    vi.stubGlobal('fetch', fetcher)
    const wrapper = mount(OperationForm, { props: { operation: 'createProject', schemaName: 'ProjectCreate', params: {}, preset: { name: '夹具项目', description: '' }, refresh: async () => {}, saved: async () => {} }, global })
    await settle(); await wrapper.get('form').trigger('submit'); await settle(); expect(wrapper.text()).toContain('同一操作重试')
    await settle(); await wrapper.get('form').trigger('submit'); await settle(); expect(wrapper.text()).toContain('请重新填写名称'); expect(wrapper.emitted('close')).toBeUndefined()
    expect(fetcher.mock.calls[0]![1].headers['Idempotency-Key']).toBe(fetcher.mock.calls[1]![1].headers['Idempotency-Key']); expect(fetcher.mock.calls[0]![1].body).toBe(fetcher.mock.calls[1]![1].body)
    wrapper.unmount()
  })
  it('blocks missing proof, checks fill content without performing the write, and renders every real business form', async () => {
    const { calls } = fixtureFetch()
    const wrapper = mount(OperationForm, { props: { operation: 'transitionTask', schemaName: 'BlockTransition', params: { project_id: 1, task_id: 1 }, preset: { expected_version: 1, action: 2 }, refresh: async () => {}, saved: async () => {} }, global })
    await settle(); await wrapper.get('form').trigger('submit'); expect(wrapper.text()).toContain('请检查必填项'); expect(calls).toHaveLength(0); wrapper.unmount()
    const check = mount(OperationForm, { props: { operation: 'transitionTask', schemaName: 'StartTransition', params: { project_id: 1, task_id: 1 }, preset: { expected_version: 1, action: 1 }, refresh: async () => {}, saved: async () => {} }, global })
    await settle(); await button(check, '检查填写内容').trigger('click'); await settle(); expect(calls[0]!.path).toBe('/api/v1/projects/1/contract-validations'); expect(check.emitted('close')).toBeUndefined(); check.unmount()
    for (const [operation, schemaName] of Object.entries(formSchemas)) {
      const form = mount(OperationForm, { props: { operation, schemaName, params: { project_id: 1, task_id: 1 }, preset: presets(operation, operation === 'changeIteration' ? iteration : member, task), refresh: async () => {}, saved: async () => {} }, global })
      await settle(); expect(form.find('form').exists()).toBe(true); await button(form, '取消').trigger('click'); expect(form.emitted('close')).toHaveLength(1); form.unmount()
    }
  })
})
describe('session and user flows', () => {
  it('logs in with transient password, hydrates workspace, clears password on rejection and success', async () => {
    workspace.user = null
    const { fetcher } = fixtureFetch()
    const wrapper = mount(LoginView, { global })
    await settle(); await wrapper.get('form').trigger('submit'); expect(wrapper.text()).toContain('请填写账号和密码')
    await wrapper.get('#login-username').setValue('fixture-user'); await wrapper.get('#login-password').setValue('synthetic-password')
    fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ message: '账号或密码错误' }), { status: 401 }))
    await settle(); await wrapper.get('form').trigger('submit'); await settle(); expect(wrapper.get('#login-password').element).toHaveProperty('value', '')
    await wrapper.get('#login-password').setValue('synthetic-password'); await wrapper.get('form').trigger('submit'); await settle(); expect(asRow(workspace.user).id).toBe(user.id); expect(wrapper.get('#login-password').element).toHaveProperty('value', ''); wrapper.unmount()
  })
  it('shows project selection, iteration edits, personal notification read/handling separately, audit and rules', async () => {
    for (const area of ['projects', 'schedule', 'notifications', 'audit', 'overview', 'tasks', 'reviews'] as const) {
      const wrapper = mount(WorkspaceView, { props: { page: area }, global }); await settle()
      expect(wrapper.findAll('.business-card').length).toBeGreaterThan(0)
      if (area === 'projects') { await button(wrapper, '创建项目').trigger('click'); expect(wrapper.text()).toContain('确认创建项目'); await button(wrapper, '取消').trigger('click'); await button(wrapper, '管理当前项目成员').trigger('click'); await settle(); await button(wrapper, '添加已有账号').trigger('click'); expect(wrapper.text()).toContain('添加成员'); await button(wrapper, '取消').trigger('click'); await button(wrapper, '调整角色').trigger('click'); expect(wrapper.text()).toContain('调整成员角色'); await button(wrapper, '取消').trigger('click'); await button(wrapper, '移除成员').trigger('click'); expect(wrapper.text()).toContain('移除成员'); await button(wrapper, '取消').trigger('click') }
      if (area === 'schedule') { await button(wrapper, '调整迭代与容量').trigger('click'); expect(wrapper.text()).toContain('人力容量'); await button(wrapper, '取消').trigger('click') }
      if (area === 'notifications') {
        await button(wrapper, '标记已读').trigger('click'); expect(wrapper.find('#field-note').exists()).toBe(false); await button(wrapper, '取消').trigger('click')
        await button(wrapper, '记录处理结果').trigger('click'); expect(wrapper.find('#field-note').exists()).toBe(true); await button(wrapper, '取消').trigger('click')
        await button(wrapper, '项目升级历史').trigger('click'); await settle(); expect(wrapper.text()).toContain('收件人')
        await button(wrapper, '升级规则').trigger('click'); await settle(); expect(wrapper.text()).toContain('扫描间隔')
      }
      if (area === 'tasks') { await wrapper.get('.business-card h3 button').trigger('click'); await settle(); expect(wrapper.text()).toContain('交付操作') }
      wrapper.unmount()
    }
  })
  it('loads task details and every evidence/history tab, exposing proper operations without deciding permissions', async () => {
    const wrapper = mount(TaskDrawer, { props: { projectId: 1, taskId: 1, revision: 0 }, global }); await settle()
    await wrapper.get('#task-action').setValue('2'); await button(wrapper, '填写流转依据').trigger('click'); expect(wrapper.emitted('operate')![0]).toMatchObject(['transitionTask', 'BlockTransition', { project_id: 1, task_id: 1 }, { expected_version: 1, action: 2 }])
    for (const text of ['调整负责人', '调整任务排期', '添加前置依赖', '发布代码评审', '新建上线评估']) await button(wrapper, text).trigger('click')
    for (const text of ['前置依赖', '代码评审', '上线评估与预案', '发布与回滚决定', '升级历史', '变更与排期差异']) {
      await button(wrapper, text).trigger('click'); await settle(); expect(wrapper.findAll('.business-card')).toHaveLength(1)
      if (text === '前置依赖') await button(wrapper, '移除此依赖').trigger('click')
      if (text === '上线评估与预案') await button(wrapper, '审核此预案').trigger('click')
    }
    expect(wrapper.emitted('operate')).toHaveLength(8)
    wrapper.unmount()
  })
  it('shows read failures, empty project scopes and paginated collections without leaking stale records', async () => {
    const { fetcher } = fixtureFetch({ '/api/v1/projects/1/tasks': page([]) })
    const wrapper = mount(WorkspaceView, { props: { page: 'tasks' }, global }); await settle(); expect(wrapper.text()).toContain('暂无相关记录')
    fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ message: '此项目没有访问权限', code: 'PROJECT_ACCESS_DENIED' }), { status: 403 }))
    await button(wrapper, '刷新记录').trigger('click'); await settle(); expect(wrapper.text()).toContain('此项目没有访问权限')
    workspace.projectId = null; await settle(); expect(wrapper.text()).toContain('先选择一个项目'); wrapper.unmount()
    const records = mount(RecordList, { props: { rows: [notification], total: 40, page: 1 }, global }); await button(records, '下一页').trigger('click'); expect(records.emitted('page')).toEqual([[2]]); records.unmount()
  })
  it('integrates app navigation, project switcher, help and logout with the logged-in workspace', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [...navigation.map((item) => ({ path: item.path, component: WorkspaceView, props: { page: item.key }, meta: { title: item.label } })), { path: '/:pathMatch(.*)*', component: NotFoundView }] })
    await router.push('/'); await router.isReady()
    const wrapper = mount(App, { global: { ...global, plugins: [router] }, attachTo: document.body }); await settle()
    await wrapper.get('a.navigation__link[href="/tasks"]').trigger('click'); await settle(); expect(wrapper.get('h1').text()).toBe('交付任务')
    await button(wrapper, '访问说明').trigger('click'); await settle(); expect(wrapper.text()).toContain('记录中的时间统一显示为北京时间'); await button(wrapper, '知道了').trigger('click')
    await wrapper.get('button[aria-label="打开主导航"]').trigger('click'); await settle(); await wrapper.get('button[aria-label="关闭主导航"]').trigger('click')
    await router.push('/not-found'); await settle(); expect(wrapper.text()).toContain('页面不存在')
    await button(wrapper, '退出').trigger('click'); await settle(); expect(api.token).toBe(''); expect(wrapper.text()).toContain('登录工作空间'); wrapper.unmount()
  })
})
