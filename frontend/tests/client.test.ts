import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, intentFor, request } from '../src/api'
import { allPages, bootstrap, context, display, logout, workspace } from '../src/workspace'
import { asArray, initial, label, resolve, safeLink, schemas, validate } from '../src/contract'
import { formSchemas, presets, transitionSchema } from '../src/forms'
import { dictionaries, evidence, fixtureFetch, member, page, plan, project, seed, task, template, user } from './fixtures'
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
describe('contract-driven forms and safe records', () => {
  it('validates real typed fields and evidence without treating strings as numbers or missing proof as approval', () => {
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
    expect(presets('changeProjectMember', member).roles).toEqual([1, 2, 3]); expect(presets('changeIteration', { ...plan, name: '迭代', version: 2, capacity: [] }).expected_version).toBe(2)
    expect(presets('reviewReleaseAssessment', { version: 3 }, task).expected_assessment_version).toBe(3); expect(formSchemas.handleNotification).toBe('HandleNotificationRequest')
    expect(template.version).toBe(1); expect(dictionaries.task_states).toBeDefined()
  })
})
