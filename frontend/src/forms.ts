import { asArray, asRow, initial, resolve, schemas } from './contract'
import type { Row } from './contract'
import { options, workspace } from './workspace'

export const formSchemas: Record<string, string> = { createProject: 'ProjectCreate', addProjectMember: 'MemberCreate', changeProjectMember: 'MemberChange', removeProjectMember: 'MemberRemove', createIteration: 'IterationCreate', changeIteration: 'IterationChange', createTask: 'TaskCreate', changeTaskPlan: 'TaskPlanChange', changeTaskAssignment: 'AssignmentChange', addTaskDependency: 'DependencyCreate', removeTaskDependency: 'DependencyRemove', createTaskReview: 'ReviewCreate', createReleaseAssessment: 'ReleaseAssessmentCreate', reviewReleaseAssessment: 'ReleaseAssessmentReview', markNotificationRead: 'MarkReadRequest', handleNotification: 'HandleNotificationRequest' }
export function businessRejection(status: number, code: string, operation: string, schemaName: string): { title: string; message: string } | undefined {
  if (status === 422 && code === 'CAPACITY_REFERENCE_INVALID') {
    const messages: Record<string, string> = {
      createIteration: '人力安排包含重复或无效人员。请在项目空间确认每人都是本项目有效开发成员，并在迭代排期中每人仅登记一次有效工时。',
      changeIteration: '迭代人力安排不满足保护规则：必须保留所有未结项任务（待受理、开发中、阻塞、待评审、待上线）负责人的工时，并核对人员为有效开发成员且不重复。若正在移除负责人工时，请先保留；仅允许转派状态可先转给已登记工时的开发成员，其余任务须先完成相应流程。已交付、已回滚任务允许移出迭代工时，但项目成员身份另受保护。',
      createTask: '负责人尚未登记在所选迭代的人力安排中。请先在迭代排期为该负责人登记有效工时，再返回创建任务。',
      changeTaskAssignment: '接手人尚未登记在任务当前迭代的人力安排中。请先在迭代排期为接手人登记有效工时，再在允许转派的状态执行转派。',
      ...(schemaName === 'ReworkTransition' ? { transitionTask: '返工前，原负责人必须仍是本项目有效开发成员，并已登记任务当前迭代工时。请先在项目空间核对开发角色，在迭代排期补回工时，再返回决定返工。' } : {}),
    }
    if (messages[operation]) return { title: '人力安排不符合要求', message: messages[operation] }
  }
  if (status === 422 && code === 'OWNER_NOT_PROJECT_DEVELOPER' && ['createTask', 'changeTaskAssignment'].includes(operation)) return { title: '负责人不符合要求', message: '所选负责人不是本项目有效开发成员。请先在项目空间核对成员及开发角色，再登记该迭代工时后执行。' }
  if (status === 409 && code === 'MEMBER_IN_USE' && ['changeProjectMember', 'removeProjectMember'].includes(operation)) return { title: '成员仍有关联任务', message: '该成员仍负责未结项或已回滚任务，暂不能移除成员或撤销开发角色。请保留身份，按允许状态合法处理相关任务；已回滚任务虽可移出迭代工时，仍须保留项目成员和开发角色。' }
}
export function transitionSchema(action: number): string {
  return schemas.TransitionRequest!.oneOf!.find((part) => resolve(part).properties?.action?.const === action)!.$ref!.split('/').pop()!
}
export function presets(operation: string, record: Row = {}, task: Row = {}): Row {
  const base: Row = schemas[formSchemas[operation] ?? '']?.properties?.expected_version ? { expected_version: task.version ?? record.version ?? null } : {}
  if (operation === 'createTask') return { dependency_task_ids: [], plan: initial(schemas.Plan!) }
  if (operation === 'changeTaskPlan') return { ...base, plan: task.plan! }
  if (operation === 'changeTaskAssignment') return { ...base, owner_id: task.owner_id! }
  if (operation === 'changeProjectMember') return { ...base, roles: record.roles! }
  if (operation === 'changeIteration') return { ...base, plan: record.plan! }
  if (operation === 'createTaskReview') return { ...base, template_version: workspace.template.version ?? null, artifact_revision: task.artifact_revision ?? '', sections: asArray(workspace.template.sections).map(asRow).map((s) => ({ section_id: s.section_id!, content: '', evidence: [] })), checklist: asArray(workspace.template.items).map(asRow).map((s) => ({ item_id: s.item_id!, judgment: null, rationale: '', evidence: [] })) }
  if (operation === 'createReleaseAssessment') return { ...base, risks: options('perspective').map((p) => ({ ...asRow(initial(schemas.RiskItem!)), perspective: p.value! })) }
  if (operation === 'reviewReleaseAssessment') return { ...base, expected_assessment_version: record.version! }
  return base
}
