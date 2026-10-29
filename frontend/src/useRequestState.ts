import { onUnmounted, ref, shallowRef } from 'vue'
import { api, ApiError } from './api'

export function useRequestState<Failure = ApiError>() {
  const busy = ref(false)
  const failure = shallowRef<Failure | null>(null)
  let active = true, sequence = 0
  const isActive = () => active
  const invalidate = () => { sequence++ }
  onUnmounted(() => { active = false; invalidate() })
  async function run(load: (current: () => boolean) => Promise<void>): Promise<void> {
    if (!active) return
    const token = api.token, request = ++sequence
    const current = () => active && request === sequence && api.token === token
    busy.value = true; failure.value = null
    try { await load(current) }
    catch (cause) { if (current()) failure.value = cause as Failure }
    finally { if (request === sequence) busy.value = false }
  }
  return { busy, failure, run, isActive, invalidate }
}
