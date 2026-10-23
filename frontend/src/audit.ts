import { asArray, asRow } from './contract'
import type { Row } from './contract'

export function auditReason(record: Row): { text?: string; missing: boolean } | undefined {
  if (typeof record.operation_id !== 'string' || record.outcome !== 1 && record.outcome !== 2 || !Array.isArray(record.after)) return
  const reasons = record.after.map(asRow).filter(item => item.field === 'reason')
  const value = reasons.length === 1 ? reasons[0]!.value : undefined
  const text = typeof value === 'string' && value.trim() && Array.from(value).length <= 2000 ? value : undefined
  const state = (items: Row['before'], expected: string): boolean => {
    const values = asArray(items).map(asRow).filter(item => item.field === 'state')
    return values.length === 1 && values[0]!.value === expected
  }
  const related = record.outcome === 1 && (['changeTaskPlan', 'changeIteration'].includes(record.operation_id) || record.operation_id === 'transitionTask' && state(record.before, '7') && state(record.after, '2'))
  return { text, missing: related && text === undefined }
}
