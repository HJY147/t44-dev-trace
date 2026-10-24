# M6冻结HTTP操作输入输出表

直接从1.1冻结OpenAPI提取，38操作/130 Schema；路径前缀/api/v1。输入参数仍受项目权限/业务状态/事务守卫，列出Schema不等于已执行全错误矩阵。精确JSON见specs/contracts/openapi.json。

| operation | 方法 路径 | 输入 | 成功输出 | 声明HTTP错误 |
| --- | --- | --- | --- | --- |
| login | POST /auth/login | ；body LoginRequest | 200:LoginEnvelope | 400,401,413,422,429,503,500 |
| logout | POST /auth/logout | 无body | 200:AckEnvelope | 401,503,500 |
| getMe | GET /auth/me | 无body | 200:UserEnvelope | 401,403,503,500 |
| getDictionaries | GET /dictionaries | 无body | 200:DictionariesEnvelope | 401,403,503,500 |
| createProject | POST /projects | ；body ProjectCreate | 201:ProjectEnvelope | 400,401,403,409,413,422,503,500 |
| listProjects | GET /projects | 无body | 200:ProjectPageEnvelope | 400,401,403,422,503,500 |
| getProject | GET /projects/{project_id} | 无body | 200:ProjectEnvelope | 400,401,403,404,422,503,500 |
| listProjectMembers | GET /projects/{project_id}/members | 无body | 200:MemberPageEnvelope | 400,401,403,404,422,503,500 |
| addProjectMember | POST /projects/{project_id}/members | ；body MemberCreate | 201:MemberEnvelope | 400,401,403,404,409,413,422,503,500 |
| changeProjectMember | PATCH /projects/{project_id}/members/{user_id} | ；body MemberChange | 200:MemberEnvelope | 400,401,403,404,409,413,422,503,500 |
| removeProjectMember | POST /projects/{project_id}/members/{user_id}/removal | ；body MemberRemove | 200:AckEnvelope | 400,401,403,404,409,413,422,503,500 |
| createIteration | POST /projects/{project_id}/iterations | ；body IterationCreate | 201:IterationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listIterations | GET /projects/{project_id}/iterations | 无body | 200:IterationPageEnvelope | 400,401,403,404,422,503,500 |
| changeIteration | PATCH /projects/{project_id}/iterations/{iteration_id} | ；body IterationChange | 200:IterationEnvelope | 400,401,403,404,409,413,422,503,500 |
| createTask | POST /projects/{project_id}/tasks | ；body TaskCreate | 201:TaskMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listTasks | GET /projects/{project_id}/tasks | query:state; query:owner_id; query:iteration_id; query:sort | 200:TaskPageEnvelope | 400,401,403,404,422,503,500 |
| getTask | GET /projects/{project_id}/tasks/{task_id} | 无body | 200:TaskEnvelope | 400,401,403,404,422,503,500 |
| changeTaskPlan | PATCH /projects/{project_id}/tasks/{task_id}/plan | ；body TaskPlanChange | 200:TaskMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| changeTaskAssignment | PATCH /projects/{project_id}/tasks/{task_id}/assignment | ；body AssignmentChange | 200:TaskMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listTaskDependencies | GET /projects/{project_id}/tasks/{task_id}/dependencies | 无body | 200:DependencyPageEnvelope | 400,401,403,404,422,503,500 |
| addTaskDependency | POST /projects/{project_id}/tasks/{task_id}/dependencies | ；body DependencyCreate | 201:DependencyMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| removeTaskDependency | POST /projects/{project_id}/tasks/{task_id}/dependencies/{dependency_id}/removal | ；body DependencyRemove | 200:TaskMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| transitionTask | POST /projects/{project_id}/tasks/{task_id}/transitions | ；body TransitionRequest | 200:TransitionEnvelope | 400,401,403,404,409,413,422,503,500 |
| getReviewTemplate | GET /projects/{project_id}/review-template | query:version | 200:ReviewTemplateEnvelope | 400,401,403,404,422,503,500 |
| createTaskReview | POST /projects/{project_id}/tasks/{task_id}/reviews | ；body ReviewCreate | 201:ReviewMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listTaskReviews | GET /projects/{project_id}/tasks/{task_id}/reviews | 无body | 200:ReviewPageEnvelope | 400,401,403,404,422,503,500 |
| createReleaseAssessment | POST /projects/{project_id}/tasks/{task_id}/release-assessments | ；body ReleaseAssessmentCreate | 201:AssessmentMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listReleaseAssessments | GET /projects/{project_id}/tasks/{task_id}/release-assessments | 无body | 200:AssessmentPageEnvelope | 400,401,403,404,422,503,500 |
| reviewReleaseAssessment | POST /projects/{project_id}/tasks/{task_id}/release-assessments/{assessment_id}/reviews | ；body ReleaseAssessmentReview | 200:AssessmentMutationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listTaskDecisions | GET /projects/{project_id}/tasks/{task_id}/decisions | 无body | 200:DecisionPageEnvelope | 400,401,403,404,422,503,500 |
| validateContractPayload | POST /projects/{project_id}/contract-validations | ；body ContractValidationRequest | 200:ContractValidationEnvelope | 400,401,403,404,413,422,503,500 |
| getEscalationRules | GET /projects/{project_id}/escalation-rules | query:version | 200:EscalationRuleEnvelope | 400,401,403,404,422,503,500 |
| listEscalations | GET /projects/{project_id}/escalations | query:task_id; query:level | 200:EscalationPageEnvelope | 400,401,403,404,422,503,500 |
| createEscalation | POST /internal/projects/{project_id}/tasks/{task_id}/escalations | ；body EscalationRequest | 202:EscalationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listMyNotifications | GET /me/notifications | query:project_id; query:read; query:handled | 200:NotificationPageEnvelope | 400,401,403,404,422,503,500 |
| markNotificationRead | POST /projects/{project_id}/notifications/{notification_id}/read | ；body MarkReadRequest | 200:NotificationEnvelope | 400,401,403,404,409,413,422,503,500 |
| handleNotification | POST /projects/{project_id}/notifications/{notification_id}/handling | ；body HandleNotificationRequest | 200:NotificationEnvelope | 400,401,403,404,409,413,422,503,500 |
| listProjectAuditEvents | GET /projects/{project_id}/audit-events | query:task_id; query:outcome | 200:AuditPageEnvelope | 400,401,403,404,422,503,500 |

错误码取值、violations及优先级以冻结操作声明和实现为准；HTTP422既可能结构违反也可能业务拒绝，前端按状态和code展示原因。三核心候选结构校验不执行全部业务守卫，不能以valid代替正式提交。
