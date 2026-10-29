// ROLE-reviewer-PRODUCT-v1; reviewer-only reproduction, target e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef.
// Does not read independent acceptance cases. Assertions describe the frozen contract.
import { afterEach, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import OperationForm from '../../frontend/src/components/OperationForm.vue'
import { presets } from '../../frontend/src/forms'
import { workspace } from '../../frontend/src/workspace'
const settle = async () => { await flushPromises(); await nextTick(); await flushPromises() }
afterEach(() => vi.unstubAllGlobals())
it('retains the actual nested Iteration.plan when opening an iteration edit', () => {
  const actual = { id: 7, project_id: 1, version: 3, plan_version: 2, created_at: '2026-10-23T00:00:00Z', updated_at: '2026-10-23T00:00:00Z', plan: { name: '真实契约迭代', planned_start: '2026-10-23T00:00:00Z', planned_end: '2026-10-24T00:00:00Z', capacity: [{ user_id: 1, available_hours: 8 }], buffer_hours: 2, delay_contingency: '延期预案' } }
  const actualPreset = JSON.parse(JSON.stringify(presets('changeIteration', actual)))
  console.log('ITERATION_PRESET_OBSERVED', JSON.stringify(actualPreset))
  expect(actualPreset.plan).toEqual(actual.plan)
})
it('does not claim the historical replay state is the current state after authoritative refresh', async () => {
  workspace.dictionaries = { task_states: [{ value: 2, name: 'developing', label: '开发中' }, { value: 6, name: 'delivered', label: '已交付' }] }
  let currentTask = { state: 2, version: 2 }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: { task: { state: 2, version: 2 }, decision: null }, meta: { replayed: true, request_id: 'new-id', original_request_id: 'old-id' } }), { status: 200 })))
  const wrapper = mount(OperationForm, { props: { operation: 'transitionTask', schemaName: 'StartTransition', params: { project_id: 1, task_id: 1 }, preset: { expected_version: 1, action: 1 }, refresh: async () => currentTask, saved: async () => { currentTask = { state: 6, version: 9 }; workspace.notice = '已刷新：当前任务已交付，版本9' } }, global: { stubs: { teleport: true } } })
  await settle(); await wrapper.get('form').trigger('submit'); await settle()
  console.log('CURRENT_TASK_OBSERVED', JSON.stringify(currentTask), 'NOTICE_OBSERVED', workspace.notice)
  expect(currentTask.state).toBe(6)
  expect(workspace.notice).not.toContain('任务现为开发中')
  wrapper.unmount()
})
