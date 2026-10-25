Agent-Role: database (AI owner; not student manual edit)
Prompt-Ref: ROLE-database-SIZE-OPTIMIZE-20261025-v1

实际规模补丁已提交/push：稳定兼容版本 c434a0b + 5f779388（分支 codex/database-size-optimize-20261025），新 VERSION2 seed 候选设计43d8f14、产品1076677527bbfc94e376ce1a564fc461622b5dee（codex/database-seed-v2-optimize-20261025）。根负责精确源码审核/组合CI与是否采用V2，不自行发布review成功状态。

严格原 cloc2.10/SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83：935产品基线6335；当前本岗1076677实际6245，净90，--require-range真实exit1，仍超5100。持久Python逐项1691→1601；稳定版本省68，V2另22。目标400–500/另80–120均未达到，不把目标或未采用候选预扣。首批手算1791/350/48曾错误，原JSON始终1691/349/49，现报告以原工具JSON为准。

实际改动：seed共用fixture上下文/JSON证据注解、迁移共用索引/unique目录与完成核对路径、Rows比较与结果集合校验、pending优先再expired租约claim共用扫描，以及冻结DDL默认值唯一来源。全部已有模块函数/方法签名静态逐项相同，specs、backend/migrations和frozenDDL净变更0；无权限/guard/事务/lease/CAS删除。migrate返回/拒绝文本及SQL、commit、核对、解锁次序9场景对935差分一致；claim7场景含bool/float/零limit及优先/余量/令牌，SQL与结果对照一致。Rows原993+989为69通过，默认值差分+原980非integration为12通过/4未选。

VERSION2是根明确准入的新合成算法，CLI参数/结果形状与默认40P/6000T/9000D/15000(reviews+decisions)保留。slot时间轴使完成前驱实际交付早于后继计划开始；完整1..7状态、三个独立角色、逐轮评审、评估1/2/3、四视角风险、批准指针、交付/回滚、JSON/容量和一次事务分批顺序保留。旧marker/version或不同配置拒绝，不迁移/覆盖旧sealed数据。原975按当前VERSION选快照，V1两golden/935来源仍在；旧V1小黄金对新算法真实红留存，未替换成跑历史实现冒充当前覆盖。

新V2性质13场景33.10s通过，含真实6000任务全35FK/指针/版本/JSON/角色/时间与独立新SQLite按batch127重现；第一轮新测试误把只读UoW commit计入seed的2红保留，改为seed返回后立即核单commit。最后旧marker范围读取保护后，准确107源的975+新性质小目标14通过/2未选、原975默认6000单目标1通过/2未选25.95s（原JUnit warning保留）。集合重叠，不相加为独立用例总数。

SQLGlot30.24.0仅本岗隔离原型，425组对照无差异但完整候选仅省9、590次解析约13.4倍耗时，根同意撤回；生产/依赖清单/锁文件未改，9未计入90。正式MySQL/锁并发、新版native CHECK、完整CI/coverage、独立验收和正式性能均未由本岗执行；全局规模仍失败。

代码/原始日志、逐文件cloc、边界检查与源绑定报告在 agents/database/size-optimize-20261025/；根完整CI应另纳入 tmp/812_database_size/test_migration_order.py、test_schema_defaults.py、test_seed_v2.py。
