import { operations } from './contract'
import type { Json, Row } from './contract'

export type Envelope = { data: Json; meta: { replayed: boolean; request_id: string } }
export type Intent = { fingerprint: string; key: string }
export class ApiError extends Error {
  constructor(public status: number, public detail: Row) { super(typeof detail.message === 'string' && /[\u3400-\u9fff]/.test(detail.message) ? detail.message : ({ 401: '登录已失效，请重新登录。', 403: '当前账号没有执行此操作的项目权限。', 404: '记录不存在或已不可访问。', 409: '记录或业务条件已经变化，请刷新核对后再操作。', 422: '填写内容不符合要求，请检查字段与证据。', 503: '服务暂不可用，操作结果需要确认，请按同一操作重试。' } as Record<number, string>)[status] ?? '请求暂时未完成，请保留内容后重试。') }
}
export const api = { token: '', unauthorized: () => {} }
export function checkSession(token: string): void {
  if (api.token !== token) throw new ApiError(0, { code: 'SESSION_CHANGED', message: '会话已变化，请在当前会话刷新记录。' })
}
export function intentFor(operation: string, params: Row, body: Json, previous?: Intent): Intent {
  const fingerprint = JSON.stringify([operation, params, body])
  return previous?.fingerprint === fingerprint ? previous : { fingerprint, key: crypto.randomUUID() }
}
export async function request(operation: string, params: Row = {}, query: Row = {}, body?: Json, intent?: Intent): Promise<Envelope> {
  const token = api.token
  const op = operations[operation]!
  const path = op.path.replace(/\{(\w+)\}/g, (_, key: string) => encodeURIComponent(String(params[key])))
  const search = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== '' && v !== null).map(([k, v]) => [k, String(v)]))
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (intent) headers['Idempotency-Key'] = intent.key
  let response: Response
  try { response = await fetch(`/api/v1${path}${search.size ? '?' + search : ''}`, { method: op.method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store' }) }
  catch { throw new ApiError(0, { code: 'NETWORK_UNCERTAIN', message: '网络中断，操作结果尚待确认。请保留原内容，使用原请求重试。' }) }
  if (response.status === 401 && operation !== 'login' && api.token === token) { api.token = ''; api.unauthorized() }
  let payload: unknown
  try { payload = await response.json() } catch { throw new ApiError(response.status, { code: 'INVALID_RESPONSE', message: '服务暂未返回可识别的记录，请稍后重试。' }) }
  if (!response.ok) {
    throw new ApiError(response.status, payload as Row)
  }
  if (operation !== 'login') checkSession(token)
  return payload as Envelope
}
