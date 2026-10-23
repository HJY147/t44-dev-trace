import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, intentFor, request } from '../../frontend/src/api'
import { allPages, bootstrap, context, display, logout, workspace } from '../../frontend/src/workspace'
import { asArray, initial, label, resolve, safeLink, schemas, validate } from '../../frontend/src/contract'
import { formSchemas, presets, transitionSchema } from '../../frontend/src/forms'
import { dictionaries, envelope, evidence, fixtureFetch, iteration, member, page, plan, project, seed, task, template, user } from './981_fixtures'
beforeEach(seed)
afterEach(() => vi.unstubAllGlobals())
describe('frozen API client', () => {
  it('keeps same intent key/body for network or 503 recovery and changes it for changed content', async () => {
    const body = { expected_version: 1, action: 1 }, params = { project_id: 1, task_id: 1 }
    const first = intentFor('transitionTask', params, body)
    expect(intentFor('transitionTask', params, body, first)).toBe(first)
    expect(intentFor('transitionTask', params, { ...body, expected_version: 2 }, first).key).not.toBe(first.key)
    const mock = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(new Response(JSON.stringify({ code: 'TRANSACTION_UNCERTAIN', message: '结果待确认' }), { status: 503 })).mockResolvedValue(new Response(JSON.stringify({ data: { task }, meta: { replayed: true } })))
    vi.stubGlobal('fetch', mock)
    await expect(request('transitionTask', params, {}, body, first)).rejects.toMatchObject({ status: 0 })
    await expect(request('transitionTask', params, {}, body, first)).rejects.toMatchObject({ status: 503 })
    expect((await request('transitionTask', params, {}, body, first)).meta.replayed).toBe(true)
    for (const [url, init] of mock.mock.calls) { expect(url).toBe('/api/v1/projects/1/tasks/1/transitions'); expect(url).not.toContain(api.token); expect(init.headers['Idempotency-Key']).toBe(first.key); expect(init.body).toBe(JSON.stringify(body)) }
  })
  it('clears memory identity on 401, handles malformed responses, and encodes query filters', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ message: '无权限', code: 'ACTION_FORBIDDEN' }), { status: 403 })).mockResolvedValueOnce(new Response('bad', { status: 401 })).mockResolvedValueOnce(new Response('bad', { status: 502 })))
    await expect(request('getMe')).rejects.toMatchObject({ status: 403 }); expect(api.token).not.toBe('')
    await expect(request('getMe')).rejects.toBeInstanceOf(ApiError); expect(api.token).toBe(''); expect(workspace.user).toBeNull()
    await expect(request('getMe')).rejects.toMatchObject({ status: 502 })
    const { fetcher } = fixtureFetch(); await request('listTasks', { project_id: 1 }, { state: 2, page: 1, owner_id: null, iteration_id: '' }); expect(String(fetcher.mock.calls[0]![0])).toBe('/api/v1/projects/1/tasks?state=2&page=1')
  })
  it('hydrates real contexts, pages collections without truncating, and logs out only after server acknowledgement', async () => {
    const { fetcher } = fixtureFetch()
    await bootstrap(); await context(); expect(workspace.project.name).toBe(project.name); expect(workspace.template.version).toBe(1)
    expect(display(2, 'state')).toBe('开发中'); expect(display(1, 'owner_id')).toBe(user.display_name); expect(display(null)).toBe('—'); expect(display(true)).toBe('是'); expect(display(false)).toBe('否'); expect(display('2026-10-23T00:00:00Z')).toContain('08:00')
    fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ data: { ...page([project]), total: 2 } }))).mockResolvedValueOnce(new Response(JSON.stringify({ data: { ...page([{ ...project, id: 2 }]), total: 2 } })))
    expect(await allPages('listProjects')).toHaveLength(2)
    await logout(); expect(api.token).toBe(''); expect(workspace.user).toBeNull()
    workspace.projectId = null; await context(); expect(workspace.members).toEqual([])
  })
  it('does not hide normal project data when optional template/rule loading fails', async () => {
    const { fetcher } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    fetcher.mockImplementation(async (url, init) => String(url).endsWith('/escalation-rules') ? new Response(JSON.stringify({ message: '暂不可用' }), { status: 503 }) : base(url, init))
    await context(); expect(workspace.project.id).toBe(1); expect(workspace.contextWarning).toContain('暂不可用')
  })
})
describe('session cleanup boundaries', () => {
  const expectEmptyContext = () => expect({ ...workspace, notice: '' }).toEqual({ user: null, projectId: null, project: {}, projects: [], members: [], iterations: [], taskChoices: [], dictionaries: {}, template: {}, rules: {}, contextWarning: '', notice: '' })
  it('clears every session context after acknowledged logout', async () => {
    fixtureFetch(); workspace.contextWarning = '旧项目提示'
    await logout()
    expectEmptyContext(); expect(api.token).toBe(''); expect(workspace.notice).toBe('已退出当前会话。')
  })
  it('clears every session context on a current-session non-login 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: '会话过期' }), { status: 401 })))
    await expect(request('getMe')).rejects.toMatchObject({ status: 401 })
    expectEmptyContext(); expect(workspace.notice).toContain('登录已失效')
  })
  it.each([0, 503])('retains identity and project when logout fails with %s', async status => {
    vi.stubGlobal('fetch', status ? vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: '服务暂不可用' }), { status })) : vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(logout()).rejects.toMatchObject({ status })
    expect(api.token).toBe('fixture-token-not-a-real-credential'); expect(workspace.user?.id).toBe(user.id); expect(workspace.project.name).toBe(project.name)
  })
  it('does not allow a late previous-session 401 to revoke a new session', async () => {
    let respond!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(resolve => { respond = resolve })))
    const pending = request('getMe'); const rejected = expect(pending).rejects.toMatchObject({ status: 0, detail: { code: 'SESSION_CHANGED' } })
    api.token = 'new-fixture-session'; workspace.user = { ...user, id: 2 }
    respond(new Response(JSON.stringify({ message: '旧会话已失效' }), { status: 401 })); await rejected
    expect(api.token).toBe('new-fixture-session'); expect(workspace.user?.id).toBe(2)
  })
  it('does not hand a late successful response to a changed session, including delayed JSON decoding', async () => {
    let decode!: (payload: unknown) => void
    const response = new Response('{}'); response.json = () => new Promise(resolve => { decode = resolve })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
    const pending = request('getProject', { project_id: 1 }); const rejected = expect(pending).rejects.toMatchObject({ status: 0, detail: { code: 'SESSION_CHANGED' } })
    await Promise.resolve(); api.token = 'new-fixture-session'
    decode(envelope(project)); await rejected
    expect(api.token).toBe('new-fixture-session')
  })
  it('does not restore the previous bootstrap identity after logout and a new login', async () => {
    const { fetcher } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    let respond!: (response: Response) => void
    fetcher.mockImplementation((url, init) => String(url).endsWith('/auth/me') ? new Promise<Response>(resolve => { respond = resolve }) : base(url, init))
    const pending = bootstrap().catch(() => {})
    await logout(); api.token = 'new-fixture-session'; workspace.user = { ...user, id: 2 }; workspace.projects = [{ ...project, name: '新会话项目' }]
    respond(new Response(JSON.stringify(envelope(user)))); await pending
    expect(workspace.user?.id).toBe(2); expect(workspace.projects[0]?.name).toBe('新会话项目')
  })
  it('does not restore a same-project old context after logout and a new login', async () => {
    const { fetcher } = fixtureFetch(); const base = fetcher.getMockImplementation()!
    let respond!: (response: Response) => void
    fetcher.mockImplementation((url, init) => String(url).endsWith('/projects/1') ? new Promise<Response>(resolve => { respond = resolve }) : base(url, init))
    const pending = context().catch(() => {})
    await logout(); api.token = 'new-fixture-session'; workspace.user = { ...user, id: 2 }; workspace.projectId = 1; workspace.project = { ...project, name: '新会话上下文' }
    respond(new Response(JSON.stringify(envelope(project)))); await pending
    expect(workspace.project.name).toBe('新会话上下文'); expect(workspace.members).toEqual([])
  })
  it.each([403, 409, 422, 503])('discards a late previous-session HTTP %s before current-session error recovery', async status => {
    let respond!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(resolve => { respond = resolve })))
    const pending = request('createProject', {}, {}, { name: '旧会话待创建', description: '' }); const rejected = expect(pending).rejects.toMatchObject({ status: 0, detail: { code: 'SESSION_CHANGED' } })
    api.token = 'new-fixture-session'; workspace.user = { ...user, id: 2 }
    respond(new Response(JSON.stringify({ message: '旧操作错误' }), { status })); await rejected
    expect(api.token).toBe('new-fixture-session'); expect(workspace.user?.id).toBe(2)
  })
})
describe('contract-driven forms and safe records', () => {
  it('leaves text and unspecified schemas empty while preserving explicit boolean and const values', () => {
    expect(initial({ type: 'string' })).toBe('')
    expect(initial({})).toBe('')
    expect(initial({ type: 'boolean' })).toBe(false)
    expect(initial({ type: 'boolean', const: true })).toBe(true)
    expect(initial({ type: 'string', const: '' })).toBe('')
    expect(initial(schemas.TaskCreate!)).toMatchObject({ title: '', description: '', plan: { delay_contingency: '' } })
  })
  it('validates real typed fields and evidence without treating strings as numbers or missing proof as approval', () => {
    expect(envelope({}).meta.contract_version).toBe(schemas.Meta!.properties!.contract_version!.const)
    expect(validate('StartTransition', { expected_version: '1', action: 1 })).not.toEqual({})
    expect(validate('StartTransition', { expected_version: 1, action: 1 })).toEqual({})
    expect(validate('EvidenceRef', { kind: 1, locator: 'src/example.py', description: '版本缺失' })).not.toEqual({})
    expect(validate('EvidenceRef', evidence)).toEqual({})
    expect(initial({ type: 'boolean' })).toBe(false); expect(initial({ type: 'number' })).toBeNull(); expect(resolve({ anyOf: [{ type: 'null' }, { type: 'string' }] }).type).toBe('string')
    expect(safeLink('javascript:alert(1)')).toBeNull(); expect(safeLink('https://u:p@example.com')).toBeNull(); expect(safeLink('https://example.com/evidence')).toContain('https://')
    expect(label('unrecognized')).toBe('补充信息')
  })
  it('seeds eight sections, ten checklist items, four risks from server values and all nine frozen actions', () => {
    const review = presets('createTaskReview', {}, task)
    expect(asArray(review.sections)).toHaveLength(8); expect(asArray(review.checklist)).toHaveLength(10); expect(asArray(review.checklist)[0]).toMatchObject({ judgment: null, evidence: [] })
    expect(asArray(presets('createReleaseAssessment', {}, task).risks)).toHaveLength(4)
    for (let action = 1; action <= 9; action++) expect(schemas[transitionSchema(action)]!.properties!.action!.const).toBe(action)
    expect(presets('createProject')).toEqual({}); expect(presets('createTask').dependency_task_ids).toEqual([])
    expect(presets('changeTaskPlan', {}, task).plan).toEqual(plan); expect(presets('changeTaskAssignment', {}, task).owner_id).toBe(1)
    expect(presets('changeProjectMember', member).roles).toEqual([1, 2, 3])
    expect(presets('reviewReleaseAssessment', { version: 3 }, task).expected_assessment_version).toBe(3); expect(formSchemas.handleNotification).toBe('HandleNotificationRequest')
    expect(template.version).toBe(1); expect(dictionaries.task_states).toBeDefined()
  })
  it('uses the frozen nested iteration plan without losing capacity or version', () => {
    expect(validate('Iteration', iteration)).toEqual({})
    expect(JSON.parse(JSON.stringify(presets('changeIteration', iteration)))).toEqual({ expected_version: 3, plan: iteration.plan })
  })
})
