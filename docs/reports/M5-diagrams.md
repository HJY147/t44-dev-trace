# M5 新增图源与来源边界

Agent-Role documentation；Prompt-Ref ROLE-documentation-M5-REPORTS-v1。内容截止6ba9f94。三图由文档AI按冻结1.1及已提交真实代码补画，不倒填为开发前已存在的图；M3八图原件及manifest不修改、不重渲染。

三图已在root明确授权窗口真实渲染并逐张打开PNG检查，六个SVG/PNG均exit0。启动18:40:14.688629 UTC，CLI完成且新增headless Chrome全部退出18:40:19.449500 UTC，耗时4.76秒；[原始日志与hash清单](diagrams/M5-render-manifest.json)保留。中文/节点箭头/标签完整、无遮挡裁切，属于成图检查，非Word逐页QA。此前两次收到窗口时余时不足，未启动/未补跑，过程记本岗日志。未调用LO/Word或重复marker。

## 1 容量生命周期

![当前真实图](diagrams/m5-capacity-lifecycle.svg)

[PNG](diagrams/m5-capacity-lifecycle.png) · [可编辑图源](diagrams/m5-capacity-lifecycle.mmd)

D005/D006、冻结capacity-lifecycle-v1.1；services/tasks.py、projects.py和workflow.py。流程图不是新增任务状态，不取代完整错误优先顺序。

```mermaid
flowchart TB
  Gate[先通过既有鉴权 幂等 状态与版本前置] --> Op{工时相关操作}
  Op -->|创建或允许阶段转派| Owner[接任人是有效developer]
  Owner --> Capacity{接任人在当前迭代capacity中}
  Capacity -->|是| Write[进入原成功事务与CAS]
  Capacity -->|否| Reject[CAPACITY_REFERENCE_INVALID 不写任务]
  Op -->|修改迭代计划| Set[读取该迭代状态1至5全部负责人]
  Set --> Keep{新capacity包含全部负责人}
  Keep -->|是| Write
  Keep -->|否| Reject
  Op -->|已回滚7返工到2| Restore[先恢复有效developer和当前迭代capacity]
  Restore --> Guard[核对既有返工证据与依赖守卫]
  Guard --> Write
  Note[6已交付和7已回滚可移出工时
项目成员和开发角色保护仍含1至5及7] -.-> Set
```

## 2 需求变更到冻结实现测试链

![当前真实图](diagrams/m5-change-to-evidence.svg)

[PNG](diagrams/m5-change-to-evidence.png) · [可编辑图源](diagrams/m5-change-to-evidence.mmd)

v1.1冻结清单、容量限定审查、4c20与5dcb发布证据。早期本地草稿的披露不被删除，开发CI不等于独立验收。

```mermaid
flowchart TB
  Human[用户U015及U016
D005与D006明确业务取舍] --> Requirement[42d3515需求与业务变更
DB705e和BE90e合同同步]
  Requirement --> Review[bbc4设计准入与59daa冻结前复核
保留失败和夹具勘误]
  Review --> Freeze[189dc4a冻结1.1.0
14文件摘要及1.0父链]
  Freeze --> Code[4c20正式容量守卫实现
本地早期草稿披露另存]
  Code --> CI[开发CI394零失败错误跳过
模块与并发回归]
  Code --> IAT[独立v2固定4c20
38成功操作与部分API断言]
  CI --> Remaining[精确新SHA仍需审核
性能 规模和整体验收未通过]
  IAT --> Remaining
  Freeze --> RFC[3187单接口读UoW设计
未改14冻结文件]
  RFC --> Next[5dcb实现及412开发CI
不能套给独立4c20结果]
  Next --> Remaining
```

## 3 当前真实UI导航

![当前真实图](diagrams/m5-ui-navigation.svg)

[PNG](diagrams/m5-ui-navigation.png) · [可编辑图源](diagrams/m5-ui-navigation.mmd)

精确75c3468的App.vue、navigation.ts、router.ts、WorkspaceView.vue。是工作区七入口，非资源级权限深链；后端鉴权不由图中登录外观证明。

```mermaid
flowchart TB
  App[App.vue及共享workspace] --> Identity{workspace.user已加载}
  Identity -->|否| Login[LoginView覆盖登录
主app-shell为inert]
  Identity -->|是| Nav[同一导航源
桌面侧栏与手机抽屉]
  Nav --> A[工作台 /]
  Nav --> B[项目空间 /projects]
  Nav --> C[交付任务 /tasks]
  Nav --> D[迭代排期 /schedule]
  Nav --> E[评审与发布 /reviews]
  Nav --> F[通知中心 /notifications]
  Nav --> G[审计记录 /audit]
  A & B & C & D & E & F & G --> View[WorkspaceView接收page prop
表单与TaskDrawer复用业务组件]
  View --> API[api.request到同源/api/v1
服务端执行权限与业务守卫]
  Unknown[未匹配路径] --> NotFound[NotFoundView
不提供资源级权限深链保证]
```

