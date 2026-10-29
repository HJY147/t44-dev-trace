# 当前38操作接口索引

产品源356f29983c904e949245aedfad464efc1bf7b63d，契约1.2.0；从冻结OpenAPI静态提取，完整错误条件保留在原契约，不把列举当已运行验证。

| 操作 | 方法与路径 | 参数和输入 | 成功输出 | 错误来源 |
| --- | --- | --- | --- | --- |
| login | POST /auth/login | LoginRequest | 200:LoginEnvelope | HTTP 400,401,413,422,429,503,500；原x-error-cases |
| logout | POST /auth/logout | 无body | 200:AckEnvelope | HTTP 401,503,500；原x-error-cases |
| getMe | GET /auth/me | 无body | 200:UserEnvelope | HTTP 401,403,503,500；原x-error-cases |
| getDictionaries | GET /dictionaries | 无body | 200:DictionariesEnvelope | HTTP 401,403,503,500；原x-error-cases |
| createProject | POST /projects | header.Idempotency-Key, ProjectCreate | 201:ProjectEnvelope | HTTP 400,401,403,409,413,422,503,500；原x-error-cases |
| listProjects | GET /projects | query.page, query.page_size, 无body | 200:ProjectPageEnvelope | HTTP 400,401,403,422,503,500；原x-error-cases |
| getProject | GET /projects/{project_id} | path.project_id, 无body | 200:ProjectEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| listProjectMembers | GET /projects/{project_id}/members | path.project_id, query.page, query.page_size, 无body | 200:MemberPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| addProjectMember | POST /projects/{project_id}/members | path.project_id, header.Idempotency-Key, MemberCreate | 201:MemberEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| changeProjectMember | PATCH /projects/{project_id}/members/{user_id} | path.project_id, path.user_id, header.Idempotency-Key, MemberChange | 200:MemberEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| removeProjectMember | POST /projects/{project_id}/members/{user_id}/removal | path.project_id, path.user_id, header.Idempotency-Key, MemberRemove | 200:AckEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| createIteration | POST /projects/{project_id}/iterations | path.project_id, header.Idempotency-Key, IterationCreate | 201:IterationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listIterations | GET /projects/{project_id}/iterations | path.project_id, query.page, query.page_size, 无body | 200:IterationPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| changeIteration | PATCH /projects/{project_id}/iterations/{iteration_id} | path.project_id, path.iteration_id, header.Idempotency-Key, IterationChange | 200:IterationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| createTask | POST /projects/{project_id}/tasks | path.project_id, header.Idempotency-Key, TaskCreate | 201:TaskMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listTasks | GET /projects/{project_id}/tasks | path.project_id, query.page, query.page_size, query.state, query.owner_id, query.iteration_id, query.sort, 无body | 200:TaskPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| getTask | GET /projects/{project_id}/tasks/{task_id} | path.project_id, path.task_id, 无body | 200:TaskEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| changeTaskPlan | PATCH /projects/{project_id}/tasks/{task_id}/plan | path.project_id, path.task_id, header.Idempotency-Key, TaskPlanChange | 200:TaskMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| changeTaskAssignment | PATCH /projects/{project_id}/tasks/{task_id}/assignment | path.project_id, path.task_id, header.Idempotency-Key, AssignmentChange | 200:TaskMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listTaskDependencies | GET /projects/{project_id}/tasks/{task_id}/dependencies | path.project_id, path.task_id, query.page, query.page_size, 无body | 200:DependencyPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| addTaskDependency | POST /projects/{project_id}/tasks/{task_id}/dependencies | path.project_id, path.task_id, header.Idempotency-Key, DependencyCreate | 201:DependencyMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| removeTaskDependency | POST /projects/{project_id}/tasks/{task_id}/dependencies/{dependency_id}/removal | path.project_id, path.task_id, path.dependency_id, header.Idempotency-Key, DependencyRemove | 200:TaskMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| transitionTask | POST /projects/{project_id}/tasks/{task_id}/transitions | path.project_id, path.task_id, header.Idempotency-Key, TransitionRequest | 200:TransitionEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| getReviewTemplate | GET /projects/{project_id}/review-template | path.project_id, query.version, 无body | 200:ReviewTemplateEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| createTaskReview | POST /projects/{project_id}/tasks/{task_id}/reviews | path.project_id, path.task_id, header.Idempotency-Key, ReviewCreate | 201:ReviewMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listTaskReviews | GET /projects/{project_id}/tasks/{task_id}/reviews | path.project_id, path.task_id, query.page, query.page_size, 无body | 200:ReviewPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| createReleaseAssessment | POST /projects/{project_id}/tasks/{task_id}/release-assessments | path.project_id, path.task_id, header.Idempotency-Key, ReleaseAssessmentCreate | 201:AssessmentMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listReleaseAssessments | GET /projects/{project_id}/tasks/{task_id}/release-assessments | path.project_id, path.task_id, query.page, query.page_size, 无body | 200:AssessmentPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| reviewReleaseAssessment | POST /projects/{project_id}/tasks/{task_id}/release-assessments/{assessment_id}/reviews | path.project_id, path.task_id, path.assessment_id, header.Idempotency-Key, ReleaseAssessmentReview | 200:AssessmentMutationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listTaskDecisions | GET /projects/{project_id}/tasks/{task_id}/decisions | path.project_id, path.task_id, query.page, query.page_size, 无body | 200:DecisionPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| validateContractPayload | POST /projects/{project_id}/contract-validations | path.project_id, ContractValidationRequest | 200:ContractValidationEnvelope | HTTP 400,401,403,404,413,422,503,500；原x-error-cases |
| getEscalationRules | GET /projects/{project_id}/escalation-rules | path.project_id, query.version, 无body | 200:EscalationRuleEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| listEscalations | GET /projects/{project_id}/escalations | path.project_id, query.page, query.page_size, query.task_id, query.level, 无body | 200:EscalationPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| createEscalation | POST /internal/projects/{project_id}/tasks/{task_id}/escalations | path.project_id, path.task_id, header.Idempotency-Key, EscalationRequest | 202:EscalationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listMyNotifications | GET /me/notifications | query.page, query.page_size, query.project_id, query.read, query.handled, 无body | 200:NotificationPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
| markNotificationRead | POST /projects/{project_id}/notifications/{notification_id}/read | path.project_id, path.notification_id, header.Idempotency-Key, MarkReadRequest | 200:NotificationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| handleNotification | POST /projects/{project_id}/notifications/{notification_id}/handling | path.project_id, path.notification_id, header.Idempotency-Key, HandleNotificationRequest | 200:NotificationEnvelope | HTTP 400,401,403,404,409,413,422,503,500；原x-error-cases |
| listProjectAuditEvents | GET /projects/{project_id}/audit-events | path.project_id, query.page, query.page_size, query.task_id, query.outcome, 无body | 200:AuditPageEnvelope | HTTP 400,401,403,404,422,503,500；原x-error-cases |
