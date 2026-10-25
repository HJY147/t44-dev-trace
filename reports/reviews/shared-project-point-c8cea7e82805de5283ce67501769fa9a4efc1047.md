# 共享项目门与逐点任务锁：准入 fresh MySQL 开发验证

## 1. 对象与身份

固定AI审核岗，非独立验收。生产候选`c8cea7e82805de5283ce67501769fa9a4efc1047`，相对`9286c7c1c44c8f9c2ef9557abbbb67825a8bba77`仅Runtime变化。原Runtime SHA256为`8802416ee003a464a8433eed80890a1c2069550ff4717ca5e07a10cf2b840b48`，候选为`9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b`。先读原设计和点锁勘误，再读实现与上下游。只读BE源码/开发原件和root明确允许的DB本岗报告/工具；不读829（包括本scope无关的PUBLIC）或其他独立材料，不联系独立测试。

## 2. 需求映射与两处差量

原graph_lock条件和_PROJECT_LOCK九项writer集合不变。START、UNBLOCK、REWORK取project S，原成员/图/iteration/assignment等writer继续X；其他迁移不新增project门。原target/已发现pred/body predecessor的set构造不变，改为sorted(unique)逐条scalar全局唯一PK+project predicate、limit1取task X；全部完成后才进入原Business。没有缓存锁读、前移错误、删鉴权或省前驱锁。目标只为降低无交集读者的项目门串行；不宣称吞吐/P95改善或旧云502根因已解。

## 3. 源、接口与证据绑定

本岗机械逆转项目lock表达式及最后task锁节点后，整个Runtime AST与原基线相同；ids构造AST独立相同。产品backend/frontend/specs差量只有Runtime；实际BE工作树Runtime逐字同C，点锁测试与HTTP驱动也逐字同C。BE证据HEAD为`06150175d41a627e537d0a2fd80887557ba2a2bc`，22项seal bytes/SHA核对通过。原合同、DDL、Rows、Business、身份、session/claim、CAS、错误与拒绝事务无差量。额外SQL数量是K个唯一任务ID由1条变K条，净增K−1，不能用无依赖样本推及全部成本。

## 4. 授权、成员与容量边界

主流程仍session S（logout X）→owned idem X→project S/X→项目members S→task X→原子写/审计/outbox/idem。门前authenticate的普通成员读不当稳定授权；项目门后全members锁定重读，active过滤并刷新call.membership，角色由原Workflow/manager判断。成员、角色、capacity/iteration、assignment writer都在项目X之后才改变相关数据，因此不能与三类持S读者越门并行。writer先提交时reader重新看授权和有效capacity；reader先到可在writer之前线性化，不能称未来撤权或前驱回滚永久不可能。全局用户active等外部写者不是该项目门的全域证明。

跨项目/缺失task的锁查询仍带project predicate，锁读返回值丢弃；原Call.task在Business内再次核project再暴露状态/版本，拒绝audit只关联本项目真实task。BE两项404验证保留独立拒审计且task_id为空。此证明不等于MySQL对不匹配PK完全不发生短暂物理记录锁；实际访问计划/锁资源应以fresh MySQL为准。

## 5. 任务与FK锁顺序

显式Runtime task锁由一个个同步语句请求，按同一数值全序获取；每条唯一PK+项目过滤至多匹配一行。相交集合仍串行，不相交集合才可能并行。读边在project S之后，writer需X，依赖集合不会被这些writer在本次读者事务中途改动；锁全体后原Workflow按RC重读状态，前驱ROLLBACK仍因目标X与reader前驱X互斥。

Business.check_graph的旧batch X没有全局改写；它在图writer的project X下，不能与新三类project S读者并行。原非图路径、成员写者内部升级、task的secondary/clustered记录、review/assessment/schedule/decision/audit/outbox FK及auto-inc都不被这句话纳入统一全序。当前源码没有发现reader project S→X升级；audit/outbox对子任务/项目父行的FK检查仍须真实成功写路径检验。源码和SQLite不能证明这些MySQL内部锁都兼容，更不能证明全域无死锁。

## 6. 实际检查与待验证

本岗只执行Git/实际字节/SHA/AST/XML/gzip等离线核对，0新产品测试/探针/SQL/HTTP/MySQL/服务/CI/云执行。先审设计后判断：已有11个开发结构/404目标已覆盖需重复的参数轨迹，再造模拟锁测试不能证明MySQL，故本岗不重跑或另造镜像实现的探针。真实MySQL留给fresh CI。

机械复算原件：首次9项setup error（不是锁断言红），修正fixture后的9项结构failure，候选11绿及另21绿，无重复，共32个唯一SQLite开发目标。没有冒为MySQL结果。HTTP7驱动仅源审，包含disjoint、graph writer、rollback vs START/UNBLOCK、REWORK capacity/manager-role和同版本CAS；未在本岗执行。其role场景是角色降级，不等同完整active=0成员撤销race，后者实际并发证据仍未知。DB6低层用例及P_S/EXPLAIN也未运行。源码保护依据成立不填补未测竞争。

DB明确允许报告记录final工具逻辑/格式阶段；本岗核实际probe SHA`bf9bbedd1dd09196c99ca986a3072a3a506b5b9ffda38f48fc1e5dcd11af37a4`，与指定3dc源`01ffb9acf99dedb8d9c2ec93ac35199061c0505a71f6785147eea6785295f01f`整AST相同。fresh CI必须绑定实际使用版本，不能混hash。原无损gzip失败、初次diff-check exit2及随后压缩归档check0保持，不改失败原文。规模owner原口径实测6326，上限5100、超1226，仍FAIL；本岗不重跑cloc、不把开发临时文件当精简成果。

## 7. 十项检查

| 项 | 判定 | 依据 |
|---|---|---|
| 1 身份与版本 | 通过 | C/两Runtime SHA、整AST与22项seal核对 |
| 2 需求与范围 | 通过限定范围 | 仅两节点，成本K−1增量不隐去 |
| 3 接口兼容 | 静态通过 | 合同、错误、业务返回无差量 |
| 4 数据库兼容 | 静态通过，MySQL待证 | DDL/Rows/RC未改；实际计划/FK/锁待CI |
| 5 状态机 | 静态无弱化 | 原Workflow重读、领域判断、CAS保持 |
| 6 权限及成员 | 静态无弱化 | writer X、members S门后active/role重查 |
| 7 事务与并发 | 准入开发验证，未正式接受 | 显式task顺序清楚；非全局无死锁证明 |
| 8 故障及幂等 | 静态保持 | 原UoW rollback、拒审计、owner fence、ACK不明无差量 |
| 9 证据真实性 | 通过限定范围 | 9setup/9红/11+21开发绿复算，0本岗执行 |
| 10 门禁及集成 | 未通过整体门禁 | 只准入fresh MySQL开发CI，规模仍FAIL，无合并许可 |

## 8. 结论

未见这两处生产修改新增的实质静态阻断，技术上可将精确C送入fresh MySQL开发CI。此明确结论已先发root；实际权限readiness、S/S、S/X、交叉/共享前驱、EXPLAIN/P_S、业务后置及成功/拒绝事务证据仍待真实运行。出现死锁、存储5xx、意外升级或计划不符须保留失败并另审，不以重试掩盖。有限CI通过也不能升级为全域无死锁、正式400×600/270ms、产品验收、规模或合并通过。

执行编排的独立窄审绑定`81250e8887336d6af417e02e73fca5692da7f0f5`，见同目录`lock-diagnostics-81250e8887336d6af417e02e73fca5692da7f0f5.md`；不复用到修改后的新HEAD。
