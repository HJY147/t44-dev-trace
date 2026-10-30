# 2026-10-31 已锁任务行复用：整合与验证记录

操作者为总协调AI。用户要求先检查代码、修改并验证，再准备压测；课堂/REA与后续电脑安排不插队。服务器保持用户已关闭状态，本轮无SSH、云变更、负载或自动停机。

## 实际改动与否决

- 产品候选a59a90a1只复用同一主事务、同一gateway已按标量主键顺序FOR UPDATE取得的目标任务行，消除transitionTask的一次重复读取。原claim、鉴权、成员锁、版本/CAS、审计及outbox继续执行。GET、重放、无目标行和不适用路径保持原读取；禁止跨gateway复用。
- INSERT-first候选a2839e17在原生MySQL RC同key并发暴露1213死锁，数据库9c8369ec已拒绝，未整合其产品代码。
- 开发测试维护69dff6f4与13acb43a分别收紧SQLite/HTTP及原生MySQL的SQL预算，保留业务、锁顺序、DML、事务控制与重放断言；后者经过数据库责任岗明确授权。原137/3开发结果及CI795/2原始失败保留，未回写。

## 实际验证

- 数据库542b5784：自建socket-only MySQL8.4.11，实际会话READ COMMITTED。12请求竞争同任务版本，1成功、11 VERSION_CONFLICT；持久任务仅递增一次，1成功+11拒绝审计；等待行锁后看到最新提交行；跨gateway/错project拒绝；无驱动错误。原夹具漏evidence导致422完整保留，修正夹具后另开实例验证。自建实例正常关闭，未触碰其他本地实例。
- 审核e4450c5d已核产品、RC与预算维护，无额外代码阻塞；当时保留待exact CI的条件，不伪改原审核快照。
- exact 13acb43a804e717e7485091895378511fe3d9b76的GitHub product运行41111111033最终success，frontend、contracts、coverage、static四项均success。原API回执保存在agents/coordinator/locked-task-ci-20261031/CI_CURRENT.PUBLIC.json。当前运行覆盖原件继续由审核岗核验留存；旧69d的行覆盖率90.27%不能冒充新运行重新计算值。

## 整合身份

候选产品与开发测试已整合到codex/manual13-preparation-integration。整合分支此前尚未带入90b的数字SQL选择器安全分类及其开发回归，现直接cherry-pick原90b734f6，未另造实现。整合后backend/t44、tmp/backend、scripts/ci、.github/workflows、frontend/src、specs、deployment与compose.yaml逐字比较准确测试源13ac，无差异。文档068adbab也已合入，不修改以上产品/测试/配置范围。

需规与设计分别为20页8图、26页10图；实际Word SHA与文档交付manifest逐字一致，文档岗记录全部46页渲染检查。两份文档保留各自事实截止与历史版本，不能因本次整合把旧待验证内容伪装为当时已通过。学生本人手写研究报告不由AI冒充。

## 尚未完成

实际性能效果仍UNMEASURED，原p13 NP_NOT_ACCEPTED保持。新镜像构建及离线更新入口、独立测量工具完整性/新adapter与新的现场身份准入分别准备；不复用已消费p13 run/material/grant。只有这些准备完成后才通知用户开机，现场仍须核真实资源、会话、业务数据和一次性许可。400/60/600、P95≤270ms及原全部断言不降低。
