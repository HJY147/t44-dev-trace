import { asArray, asRow, initial, resolve, schemas } from './contract'
import type { Row } from './contract'
import { options, workspace } from './workspace'

export const formSchemas: Record<string, string> = { createProject: 'ProjectCreate', addProjectMember: 'MemberCreate', changeProjectMember: 'MemberChange', removeProjectMember: 'MemberRemove', createIteration: 'IterationCreate', changeIteration: 'IterationChange', createTask: 'TaskCreate', changeTaskPlan: 'TaskPlanChange', changeTaskAssignment: 'AssignmentChange', addTaskDependency: 'DependencyCreate', removeTaskDependency: 'DependencyRemove', createTaskReview: 'ReviewCreate', createReleaseAssessment: 'ReleaseAssessmentCreate', reviewReleaseAssessment: 'ReleaseAssessmentReview', markNotificationRead: 'MarkReadRequest', handleNotification: 'HandleNotificationRequest' }
export function transitionSchema(action: number): string {
  return schemas.TransitionRequest!.oneOf!.find((part) => resolve(part).properties?.action?.const === action)!.$ref!.split('/').pop()!
}
export function presets(operation: string, record: Row = {}, task: Row = {}): Row {
  const base: Row = schemas[formSchemas[operation] ?? '']?.properties?.expected_version ? { expected_version: task.version ?? record.version ?? null } : {}
  if (operation === 'createTask') return { dependency_task_ids: [], plan: initial(schemas.Plan!) }
  if (operation === 'changeTaskPlan') return { ...base, plan: task.plan! }
  if (operation === 'changeTaskAssignment') return { ...base, owner_id: task.owner_id! }
  if (operation === 'changeProjectMember') return { ...base, roles: record.roles! }
  if (operation === 'changeIteration') return { ...base, plan: Object.fromEntries(Object.keys(schemas.IterationCreate!.properties!).map((key) => [key, record[key]!])) }
  if (operation === 'createTaskReview') return { ...base, template_version: workspace.template.version ?? null, artifact_revision: task.artifact_revision ?? '', sections: asArray(workspace.template.sections).map(asRow).map((s) => ({ section_id: s.section_id!, content: '', evidence: [] })), checklist: asArray(workspace.template.items).map(asRow).map((s) => ({ item_id: s.item_id!, judgment: null, rationale: '', evidence: [] })) }
  if (operation === 'createReleaseAssessment') return { ...base, risks: options('perspective').map((p) => ({ ...asRow(initial(schemas.RiskItem!)), perspective: p.value! })) }
  if (operation === 'reviewReleaseAssessment') return { ...base, expected_assessment_version: record.version! }
  return base
}
