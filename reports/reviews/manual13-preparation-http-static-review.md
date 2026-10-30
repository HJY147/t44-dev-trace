# MANUAL13 本地准备代码审核

日期：2026-10-30。岗位：代码审核；不是独立黑盒验收。

## 绑定与结论

审核对象是 `.runtime/manual12-continuation-kit-20261030-058d-doc02` 离线包（位于主仓 `.agent-worktrees/` 下）。产品源为 `90b734f65ce6ee9f5c217e885bc7ea4857e32b48`。

* wrapper 源提交 `8933dd308c9d7e103e24ae28747ed6c5d8269f48`，路径 `deployment/cloud-reuse/manual12-resume-prepare.py`，包内 SHA256 `47771609ea1d6defc308b81c9e30bf5fae49dda531e2c1dd54343c44d7fe03e9`，与提交 blob 实测一致。
* helper 源提交 `4e470170b2bddd20f9d4696f3e67198e312f8b08`，路径 `agents/backend/manual11-maintenance/v2/cohort_maintenance.py`，包内 SHA256 `058d79cf474b590559766aeac78a2525b48841d9c1d85a74784eb7a37f6ab321`，与提交 blob 实测一致。058d79 是文件摘要，不是 Git 提交号。
* 产品 OpenAPI blob SHA256：`6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478`。

该旧包不能标为全部本地准备完成，维持 `AWAITING_FULL_HTTP_SCHEMA_REVIEW_NOT_EXECUTED`；需修复以下写前门禁与 UNKNOWN 分类，再审核实际新摘要。没有访问云、启动 SUT、登录产品、执行 HTTP、压测、读取 QA PRIVATE 或未发布独立用例。400 客户端、60 秒稳定段、600 秒正式时长标准未改变。

## 缺陷

1. **P1：完整材料资格直到解除任务后才验证。** helper 264–279 仅先查 manager/dev 登录主体、800任务快照、400任务归属/状态/版本和到期时间。90b `services/workflow.py` 在 UNBLOCK 返回开发中时读取依赖，`domain/state_machine.py` 同时要求当前 developer 项目角色、本人负责、依赖全部已交付。任务 GET 只要求项目成员，不能证明 developer 角色。后批次缺角色或不满足依赖时，前批次可已提交。更严格的现有 `runtime_support.current_inventory` 要求所有 transition_task 依赖为空；已有已交付依赖也会在修改后被材料流程拒绝。

   对照现有材料链，另须将可预先检查的全部资格前移：三个原人类账号真实登录；其 `/projects` 恰好原40项目且逐项目具有 manager=1、developer=2、reviewer=3；40项目规则等于90b冻结规则且同版本；400原升级事件存在并正确绑定项目/任务/schedule_version/rule_version，任务非终态；当前至+900秒两端点的升级窗口均匹配原事件 level；原 service 账号存在、active、名称属于原 namespace。service 只读检查可由 wrapper 已有 API 容器探针承担。后续真实 token 签发、持久化、轮换、scan、最终时间漂移仍须保留后验门禁，不能宣称预检能够保证成功。

2. **P1：wrapper 未在业务写前核对旧 packet 原始表总数。** `check_probe` 117–127 只比已有 index、800 IDs、400状态，before 未与 packet.counts 比对；以后都与这个可能已漂移的 before 比。`refresh_core.build_packet` 才检查 `counts == old['counts']`，届时400解除可能已提交。按既有映射 projects/tasks/dependencies/reviews/decisions 对应 projects/tasks/task_dependencies/reviews/decisions，在解除之前拒绝总数漂移。

3. **P2：POST 200 后部分异常成功响应误分类 GUARD。** helper 291–294 先 `check_task`，其中 scope/owner/版本合法性/可恢复状态异常抛默认 GUARD，未进入后续 UNKNOWN 分支。请求可能已经提交。应将所有 mutation 成功响应解析/断言异常统一 UNKNOWN，保留 prefix 并进入只读 inspect，禁止自动再发。wrapper 当前均 no-retry，减轻但不消除错误回执分类问题。

## 已核对的接口与安全行为

真实90b路由统一前缀 `/api/v1`。login POST 返回200的 LoginEnvelope，GET tasks/task 返回200的 TaskPageEnvelope/TaskEnvelope，POST transitions 返回200的 TransitionEnvelope，GET audit-events 返回 AuditPageEnvelope。helper 使用的 page/page_size=100、audit 的 task_id/outcome 查询均为真实参数。Unblock 的 expected_version/action=3/basis/evidence(kind=2,locator,description) 与冻结 UnblockTransition 一致；响应 task、audit_id 及 state=2/blocked_from_state=null/version+1 的判断方向正确。完整 schema 未在本机运行 jsonschema 校验（系统 Python 缺该依赖），没有把人工对照写成产品 HTTP 通过。

原 packet 的 canonical binding、90b identity、旧 manifest/import/CA 摘要、400 client IDs、800互异任务IDs、40项目、原用户IDs绑定均在写前检查。新材料沿用原 IDs，不创建任务、不 seed、不执行 DDL。maintenance 登录 token 仅留内存，不记录口令或原 login body；普通响应保留私有原始字节。原任务/项目范围与行版本读取方向正确，800前后快照及升级任务完整相等断言存在。

审计恢复查询的真实 operation_id=`transitionTask`、actor_kind=1、outcome=1、expected_version、evidence locator 字段均符合90b；未确认的动作只有唯一匹配审计及当前state/version共同证明才标 POST_COMMIT_PROVEN。未见自动重放，状态未变也不宣称没有提交。正常路径仅验证响应 audit_id，不单独 GET 每条审计；它依赖90b业务成功/审计同事务保证，不应宣传为额外完成逐条审计复核。

资源流程静态为：精确原7容器 ID/image/name/user/limits 检查 → 仅退休原 timer → 获明确开关才停止原 consumer/scheduler → start 原基础设施容器 → 维护 → 原材料链/token轮换 → start原workers → 原持久scanner观测 → CMS。无新建、重建、pull、build命令。其互斥依赖操作者的外部 writer 排他确认；namespace flock 只能排除同 helper，并不能证明不存在其他业务写者。

## 本地实际检查

使用 `git show` 读取确切90b路由、契约、业务/鉴权/状态机及历史 helper/wrapper blobs；Python3 hashlib 比较包字节与上述源提交。只导入工具模块并调用纯函数，没有 main、Docker、systemctl、HTTP 或数据库执行。

纯函数证据：`check_task` 对 mutation 返回错误 owner 抛 `LIVE_ORIGINAL_OWNER_MISMATCH GUARD`；`check_probe` 对正确index/ID但五张业务表总数均999999的 before 仍接受。它们是本地逻辑检查，不是400规模运行或独立验收。系统 `python` 命令不存在；改用 python3。系统 python3 的 jsonschema 导入失败，因此未运行完整 schema validator。

本审核使用提示词：总协调对 review_preparation 的原始只读审核派工及后续要求完整对照 refresh_core/runtime_support 门禁。改进理由为补充原16项部署离线检查未覆盖的真实产品接口/业务前置条件；产物就是本文。未修改任何产品或准备脚本。
