# C-P4限定复审与架构减量审计 v2

## 1. 对象、职责及结论

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-CAPACITY-AND-CATALOG-v2。固定被审完整SHA `7c27a5f62cc23db8545a28852ed01322a7e172b4`，含数据库修复`0e3e99930dcf776de1afb3509fb68cc4e2104ab0`。独立树`.agent-worktrees/review-catalog-v2`，分支`codex/review-catalog-v2`。仅两项：原C-P4复审、代码规模架构审计；不扩审此后端IAT修复，不改产品实现或原957，不执行重负载。

结论：**原C-P4的四类同名语义漏检可限定关闭；整体仍failure/not approved。** 原口径当前5886，超5100上限786。原e01失败报告/status原样保留，本轮不重写，不发任何success，不合并main。

## 2. 原问题、修复与冻结边界

e01仅比index/unique/FK/CHECK名字，会错接受不同定义。当前migrations.py显式比较索引列序/unique/排序前缀/索引类型、FK本地与目标列/目标库及动作、CHECK结构树；CHECK词法处理限定_utf8mb4/_ascii引导符、反引号、括号、字符串和运算优先级，不能靠删所有括号/空白误判等价。

修复不改冻结DDL/API。公开live source_hash与本目标migrations.py为`2f0a908e1c984502aa1e9027cec09eae92d6513972bcc0653431240d5da33d1a`；DDL包副本和权威DDL仍为c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4。此结论关闭原四类缺陷，不声称证明任意DDL等价、所有59个CHECK负测或生产库永不漂移。

## 3. 本岗原957真实复验

957与ddaa035归档逐字节相同，SHA-256 `dffd4157a681f99cbeb45a14586f8c56e2c70c9498172e485537e69b78c4979f`；原断言未改。实际命令：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend <backend自有venv>/bin/python tmp/reviewer/957_schema_semantics_probe.py`。

退出0：未变baseline18表226列passed=true；同名索引列/unique、FK目标和CHECK变异passed=false，列出真实缺陷。脚本是隔离Inspector替身，本岗没有操作真实MySQL；原e01失败输出没有被覆盖。完整argv/env/原始输出在`agents/reviewer/evidence/catalog-v2/957-rerun.json`和`957-original-rerun.log`。

## 4. 数据库公开live证据复核

逐个复算owner summary所列14份原始文件及5份源码hash，全部一致；targeted-junit原件18用例、0failure/0skip。实际执行者database岗，本岗是公开证据复核。

| owner实际t44_review变异 | 检查/重复迁移 | 恢复 |
| --- | --- | --- |
| 同名ix_tasks_project_state改列序 | index_definition拒绝，重复迁移拒绝 | 原列序恢复后18表226列接受 |
| uq_users_username去unique保留名 | index_definition/unique_set拒绝，重复迁移拒绝 | 恢复unique后接受 |
| fk_projects_creator改指service_accounts | foreign_key_definition拒绝，重复迁移拒绝 | 恢复users目标后接受 |
| ck_users_active改1=1 | check_definition拒绝，重复迁移拒绝 | 恢复IN(0,1)后接受 |

原live run1暴露MySQL ALTER索引后把字面量引导符规范化为_ascii，旧checker误拒绝；原live run2是探针同条ALTER DROP/ADD同名FK的1826错误。两次失败、实际期望JSON和修复后run3原件均保留，不虚写首次即通过。seed专属新库40项目/6000任务/9000DAG/15000评审决定、7态及全行摘要6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3等价、重复幂等/变更拒绝、7项原生负例恢复有公开记录；本岗不重复运行，不计作自己的实库或独立验收。

以上核对清单在owner-live-verification.json；完整源码/文档输入绑定target-manifest.json。

## 5. 当前规模与架构重复定位

使用原scripts/metrics/source_count.py、docs/metrics/source-counting.md、固定hash的cloc2.10，精确目标归档统计：**5886，range=false，--require-range退出1**。stage7=5866是旧快照，不能覆盖当前新增加的20行。测试/配置/部署/生成物的原分组保持，无变更分母。

当前热点：seed370、migrations321、schema117、domain五件/服务codes与workflow合计748；runtime258、workflow243、Rows237、scheduling facade205。旧83条CSS和58行domain barrel已经删除，不能再把它们算成未来收益；初步口头806行已据本次实际cloc校正为748。以下净行估计包含新增helper/类型/适配器，均是方案预算，不是已实现计数或达标承诺。

| 方案/owner | 真正删除的旧实现与替代边界 | 预计净删 | 风险/准入证据 |
| --- | --- | ---: | --- |
| A 后端，待IAT修复和诊断后排 | 合并双表示层：冻结数字码仍显式typed enum/业务错误目录；纯decide只接一个不可变、服务端装配的task/proof snapshot。删除9个中转command类、重复Gate包装/字符串id:version往返、STATE/ROLE/STAGE双向翻译；Workflow仍加载可信证明并做CAS/审计/decision。不能同时保留新旧两层 | 180–280 | 高；内部签名会变，HTTP/DDL不变。保留七态九动作、错误先后、权限、轮次/排期/非自审、所有原断言，先做行为等价原型，不能删除守卫换行数 |
| B 调度+DB | facade._run:70–104与ScanStore.start:20–52是同一run UUID/完整初值/唯一冲突/hash校验的两份事务体。抽transaction-local start_run(g,...)；Scanner短UoW与API现有UoW各自调用，返回统一run行。tick的旧心跳查询再收口recoverable并保留rule_hash过滤 | 28–47 | 中；不能让API另开事务提交run。保留同UUID异hash拒绝、竞态savepoint、run游标和重启恢复/计数 |
| C MQ+DB | OutboxStore.confirm/fallback/retry重复锁event、核owner、清lease/updated_at；内部用带expected-status+token的推进器删旧展开。consume/fallback/recover_confirmed继续共用现有_notices | 20–35 | 中；不把“confirmed、已消费、终态fallback”合成一个状态。不删晚到去重/read-handled保留/CommitUncertain或消费提交后ACK |
| D DB，仅POC，不计收益 | schema117的自研DDL切分/类型映射与migrations的CHECK Pratt语法层存在维护重复；可评估成熟MySQL AST后共用一个规范化catalog，删除旧两份语法实现 | **不计** | 高；不能拿实际反射当预期（自比自会回归C-P4）。新依赖必须锁定/许可证/方言与_ascii、函数、优先级、所有原957/956及live矩阵POC；没有POC不能承诺省行 |
| E DB/seed | 当前context/add已共享时间/项目等，pointer也已只建一次复用。剩余370大部分是必要合成结构；只评估批写工具和少量相同初值，不再虚算旧重构收益；不建议为几行引入改变事务的seed新框架 | 0–15 | 中；必须保持固定anchor全行摘要6d56…等价、40/6000/9000/15000、7态/DAG/轮次批准/证据/四视角/产能、幂等及变更拒绝；不移到scripts/config躲统计 |

A/B/C/E区间合计约208–377，仍不足786，且可能受后续修复增行影响；不把区间上限当可保证之和。现阶段优先B、C，A后置，D只能独立POC，E不夸大。按功能聚合而不是简单按文件长度删：Rows白名单/参数化/错误rollback-only，Runtime写事务内重授权与独立拒绝，outbox确认/消费/fallback，扫描run状态/游标都承担不同必需能力，不能直接删掉“看起来重复”的一次安全检查。

D候选技术参考只查官方文档；SQLGlot提供MySQL解析入口，但其官方明确解析器宽松且不等于验证器，不能由parse成功推断约束正确。[SQLGlot官方说明](https://sqlglot.com/)、[MySQL解析器](https://sqlglot.com/sqlglot/parsers/mysql.html)。本轮未安装或以新依赖替换实现，不把库外代码藏出分母来宣称达标。

## 6. 独立公开结论与本轮限制

只读已发布`reports/independent-tests/v1-blackbox-report.md`与伴随`v1-blackbox-results.json`，未跟随报告中私有证据路径，未读取tmp/independent、未联系独立实例。公开历史被测e8ceefe699951c52d4b01023b47a76b575d48c2a整体未通过：900冻结用例340通过/183断言失败/328环境阻塞/49未执行；183不等于183个产品缺陷。三批正式性能P95为3035/1908/5506ms，超过270ms，稳态失败0/吞吐达标；仅适用其报告拓扑及版本。本轮没有重跑或外推为7c27新性能结论，也不复审正在修复的IAT01–05。

本轮新运行仅原957和原规模脚本，以及资料hash/公开JUnit解析；没有执行live DDL、seed写入、全套测试、全局覆盖率或任何性能重负载。独立公开报告/JSON摘要hash在published-acceptance-reference.json。

## 7. 十项限定判定

| 项 | 判定 |
| --- | --- |
| 1 身份/版本 | 通过：固定7c27、本岗独立树、原957hash相同 |
| 2 需求/范围 | 不通过整体：5886超5100；本轮仅两项，不扩审IAT |
| 3 接口兼容 | C-P4相关接口签名/冻结API不变；A等建议尚未实施，不假称兼容验证通过 |
| 4 数据库兼容 | 原C-P4四类漏检限定关闭：957+owner live拒绝/恢复及源码hash一致 |
| 5 状态机 | 本轮未重审；A需后置行为等价验证 |
| 6 权限/秘密 | 本轮无产品改码/库写入；不得以减量删除授权/秘密保护 |
| 7 事务并发 | 原C4相关savepoint/重复迁移证据支持；B/C必须保留UoW边界，未实施不判通过 |
| 8 幂等故障 | A/B/C/E的原幂等/恢复/原断言为改造准入条件，不据方案预算判通过 |
| 9 证据真实性 | 新执行与owner实库/独立公开历史分开；原失败、原957断言不改 |
| 10 门禁合并 | failure/not approved；不发success，不重写e01状态，不合main |

## 8. 交接与后续

总协调可登记原C-P4四类漏检在本目标技术关闭；不能改成整产品通过。优先由scheduler/DB实施B、MQ/DB实施C，提交新SHA和原功能/故障证据再审；后端A待IAT修复/诊断完毕后独立排期，DB D若做必须先POC，E保留全行等价结果。未得到足够可读净删结果前继续按原政策失败，不强凑“预计足够786”。本岗只提交审核报告/日志/hand-off/prompt/证据和真实评论，不替owner改产品，报告不含自身提交SHA以免自引用。
