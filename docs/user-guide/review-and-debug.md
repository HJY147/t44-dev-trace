# 怎样审阅本项目，再自己调试

这是 AI 整理的指导材料，不是学生署名的研究正文。依据是 [R001 本人原话](../../records/reflections/R001-original.md)和[出处](../../records/reflections/R001-provenance.json)；原话原拼写不改。下面的源码位置绑定 `f103600b0e98f8d60689d2db6dfd5211a9fd0f2a`，文件哈希见[本轮索引](../../records/qa/R001-guide-sources.json)。更完整的[函数契约说明](../function-contracts.md)基点更早，读到行号变化时以本轮源码为准。

## 先决定边界，再选写法

本题要求前后端分离的单体分层，明确不做服务拆分、集群编排和多地域部署。采用一个 Python 业务包配 MySQL，便于将任务状态、审计和事件意图放在可解释的事务边界里；API、消息和扫描各有进程，不等于三个业务微服务。多岗位 agent 也是开发组织方式，不是应用的服务拆分。实际目录见[实现约定](../collaboration/implementation-layout.md)，候选对比见[架构说明](../../architecture.md)。

`class` 适合承载需要一起使用的依赖和生命周期，例如 Runtime 持有数据库工厂和业务门面；纯函数适合不接触外部资源的规则判断，例如 `decide`；UoW（一次工作单元）负责一笔数据库事务的开始、提交、失败回滚和关闭。它们解决不同问题，可以同时使用。这里没有因为 R001 举例提到 manager-based 就换成该框架。

配置现状是：业务规则用 [escalation-rules.json](../../backend/t44/resources/escalation-rules.json)、评审模板用 [review-template.json](../../backend/t44/resources/review-template.json)，两者当前版本均为 1；加载时分别做版本/结构或哈希处理。运行地址等参数从环境传入，密码/Token 保存在部署私密配置或凭据文件，不能提交到仓库。`Settings.from_env` 当前只直接读取 `DATABASE_URL` 与 `T44_SESSION_TTL_SECONDS`，`mysql_settings` 另核对 `T44_DATABASE`，消息等进程读取各自环境。不是所有参数都已外置；也没有把用户举例的 YAML 改成新选型命令。业务规则变更需留原值、新值、版本、生效时间、影响和决定者，不能直接改 JSON 后当旧版本运行。

## 用真实函数核对输入、输出和副作用

| 入口（本轮基点行号） | 读什么、返回什么 | 人需要核对的边界 |
| --- | --- | --- |
| [intentFor](../../frontend/src/api.ts#L10) / [request](../../frontend/src/api.ts#L14) | 操作/参数/JSON → 本地 Intent；再异步返回 Envelope 或抛 ApiError | 前者不发网络；后者发 HTTP。相同内容复用请求意图不代表已经提交成功 |
| [validate_request](../../backend/t44/api.py#L104) | HTTP 请求、操作定义、Call → 补充 Call 或抛 Rejected | 查请求形态；不是完整业务决定，也不提交数据库 |
| [Runtime.execute](../../backend/t44/services/runtime.py#L223) | Call、校验回调、来源 → 状态码、结果、重放标志、原请求 ID 四元组 | 身份/请求/幂等及事务编排；成功审计与事件同事务，拒绝审计另有事务，提交不确定不得直接重做整笔业务 |
| [Workflow.transitionTask](../../backend/t44/services/workflow.py#L61) | 活动数据库网关 g、Call c → task 与可选 decision | 读真实权限/任务/依赖/证据，调用纯规则后 CAS 更新；自己不 commit；不是信任客户端说“已通过” |
| [decide](../../backend/t44/domain/state_machine.py#L90) | TaskPosition、typed Command、TransitionContext → 不可变 Decision | 判断能否迁移；不写库。DomainViolation 是内部拒绝，服务层再映射冻结错误，不直接等于 HTTP 码 |
| [Call.cas](../../backend/t44/services/common.py#L143) | g、表、旧行、更新值、预期版本 → 新行 | 按 id+version 更新且核对影响一行；冲突拒绝，仍由外层事务负责提交 |
| [SqlAlchemyUnitOfWork](../../backend/t44/persistence/uow.py#L13) | 注入 Session 工厂；进入 → self，退出 → False | single-use；正常出口提交，有异常回滚并关闭；CommitUncertain 表示没有确认，不能声称一定没提交 |
| [load_rules](../../backend/t44/scheduling/rules.py#L78) / [getReviewTemplate](../../backend/t44/services/reviews.py#L17) | JSON 路径或模板查询 → 规则对象/模板字典；非法或不存在版本拒绝 | 配置有版本，模板/规则并非任意散落常量；读取配置和纯状态判断的副作用不同 |

可以按下面顺序审一项需求，再让 AI 补实现：

1. 从 FR 和已采用的 D001/D004 写清角色、数据范围、输入、成功输出及拒绝条件。不明确处列问题给本人决定；产能转派/移除正是仍待答的问题，不能替选。
2. 沿上表把 HTTP、纯判断和写库分开，标出谁鉴权、谁读可信证据、谁提交、失败如何留痕。先审公开接口和外部副作用，再进入函数内部。
3. 若以后由本人先写 `def`/类型/说明和 `# TODO`，应同时说明前置条件、错误和禁止副作用，再让 AI 填函数体。本项目现有框架由 AI 岗位实现，没有把它追记为学生先写。明确边界可以减少误解，仍可能有实现、并发或需求缺陷，不能保证无 bug。
4. 对长期复用代码逐步审阅，并核对自动测试的要求、原始失败、修复者、版本与结果。CI 通过不是独立验收，读过 AI 发现的问题也不是本人独立识别。研究正文应由本人解释实际理解和未做部分。

## VS Code 断点练习（步骤可执行，本轮尚未执行）

先做无数据库的 `decide` 示例，避免在 API 持锁事务中长时间暂停。以下全部是 **AI 示例**；尚未创建脚本、启动解释器或给用户记操作。若要把示例保存为可运行练习，先由总协调分配 `tmp/` 递减编号，本轮未申请编号，不另建任意测试脚本。

1. 后续获分配练习路径后，在 VS Code 打开项目根，选择 Python 3.12 解释器，并确认 Python/Python Debugger 扩展可用。将下面内容保存到分配的练习文件；当前仓库没有这个现成脚本。

```python
from t44.domain.commands import StartDevelopment
from t44.domain.models import ProjectRole, TaskPosition, TaskState, TransitionContext
from t44.domain.state_machine import decide

position = TaskPosition(TaskState.PENDING)
context = TransitionContext(
    project_member=True,
    roles=frozenset({ProjectRole.DEVELOPER}),
    actor_is_owner=True,
    dependency_states=(),
)
breakpoint()  # AI 提供的暂停位置；不是退出循环
decision = decide(position, StartDevelopment(), context)
print(decision)
```

2. 在 VS Code 的“运行和调试”创建或合并以下配置，活动编辑器保持该练习文件。配置目前仅是文档示例，没有落盘或执行。

```json
{
  "version": "0.2.0",
  "configurations": [{
    "name": "T44 单个纯函数练习",
    "type": "debugpy",
    "request": "launch",
    "program": "${file}",
    "cwd": "${workspaceFolder}",
    "env": {"PYTHONPATH": "${workspaceFolder}/backend"},
    "console": "integratedTerminal",
    "justMyCode": true
  }]
}
```

3. 在 `state_machine.py` 的 `decide` 第一条可执行语句（本基点第 96 行）左侧单击设置断点。按 F5 启动上述配置；停住后看“变量”和“调用堆栈”。F10 执行下一步，F11 进入函数，继续 F5，停止用 Shift+F5。
4. 先观察 `position`、`context.roles`、`command`，再观察返回的 `decision`；把自己看到的内容和疑问记录下来。不要先改状态字段来迎合输出。示例的上下文只是人工构造的演示值，不证明真实 HTTP 权限/数据库流程通过。
5. Python 的 `breakpoint()` 会暂停供调试；用终端普通 Python 运行同一文件时通常进入 `pdb`，可用 `p position` 查看、`n` 下一步、`s` 进入、`c` 继续、`q` 退出。`break` 是结束最近一层 `for`/`while` 循环的语句，不能当断点使用；循环外写 `break` 会报语法错。
6. 更完整的 HTTP 调试再沿 `validate_request → Runtime.execute → Workflow.transitionTask → decide → Call.cas → UoW` 走。它会涉及真实事务和数据，只在明确的项目调试库/时间窗口中做，不连验收、性能或生产库；本轮性能诊断窗口内不启动这些操作。不要求上传密码、私钥或 Token。

## 本人审阅记录空表

请只填写自己实际做过的事；未做留空或写未做。不预置 12 次改码、3 条幻觉或“正确答案”。AI 已发现的缺陷可作阅读材料，但不能填成本人发现。

| 日期/准确源码版本 | 本人审阅的需求/函数 | 实际观察及问题 | 本人动作（仅审阅/改码/调试，分别写） | 原始证据与结果/未验证项 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

可自问：输入由谁信任？输出是否等于已经持久化？失败时哪些数据允许改变？重复提交和并发如何处理？测试遗漏什么？哪项取舍仍要人决定？本人独立理解了什么，哪些只是引用 AI 材料？课程建议和研究正文由本人继续写，不由本指南代填。
