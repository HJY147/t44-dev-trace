# 数据库规模优化：第一批实际补丁

基线产品935ab5b93bea788672c2b4a088c79cfeed848954，worktree父e45a2b9。没有更改DDL、public签名、外部接口或依赖。

- seed使用按需buffer，按冻结TABLES的原FK插入/锁顺序落库；相同证据注解结构和schema过滤后的fixture默认字段只有一个来源。
- migrate已应用与新建路径共用最终结构校验/返回；索引和unique共用目录构造。原错误文本、语句/commit/检查/解锁次序保留。
- Rows通过Python operator复用SQLAlchemy比较语义，递归SQL表达式拒绝统一容器遍历，有限历史结果用集合验证项目/pair/ID唯一性，保留失败rollback-only。
- Outbox pending优先再expired lease的两段相同扫描共用算法，原字段排序、残余limit、update+skip_locked、UUID token及尝试次数上限保留。包括bool limit旧拒绝行为。

原cloc2.10 SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83。逐文件原件before-cloc.json；首批最终计数另归档，初步50后为保留冻结写入次序增加2行，净减48。400–500尚未实现，不能把目标计作成果。

实际开发自测：956迁移目录语义+975小seed17通过/1大seed未选；原993+989共69通过；新迁移差分9场景加原975小/默认6000任务共12通过23.77s，两条原JUnit warning。新迁移差分基935比较返回/拒绝文本及SQL/commit/校验/解锁全序；新claim差分7场景+原980非integration组合25通过/4integration未选，含pending填满/不足/空、expired和bool/float/零limit，原marker警告保留。各集合重叠，不相加为独立案例。

原975两种固定全库语义摘要均一致，随机密码hash按旧测试规则排除。最后补回seed原冻结插入顺序后，还需针对该新变更再验证seed（未用先前结果冒充）。新增测试首次默认Ruff规则报3项C408，指定项目backend规则通过；首次PyPI下载遇本机CA缺失，不禁用TLS，改用环境certifi重试。未将环境/静态错误当产品红。

未运行真实MySQL、迁移/租约并发锁、独立验收、正式压测、完整CI或覆盖率；完整组合CI由根调度。全局规模仍超5100。SQLGlot后续原型尚未替换此首批代码。

## 第二批与明确勘误

首批手工汇总有误，原始cloc JSON没错：持久Python基线实际1691、c434a0b为1642，净减49；seed349。前文和首次发送root的1791/350/净48均是手算错误，不作为权威计量。第二批以冻结DDL的NULL/active/version/scan计数默认值为单一来源，删除19处重复初始化字段，当前1691→1623，累计净68。

初次schema-default测试Ruff I001保留于会话输出，整理import后项目限定Ruff通过；新accounts有效/拒绝审计、scan默认/UUID冲突/游标保存与终态3个SQLite差分场景和原980非integration合计12通过/4未选。首批最终锁序版975全量3通过28.12s；第二批用户active默认变更后原975小数据/回滚再2通过/1默认大数据未选（不把先前全量标成后续新源完整执行）。SQLite仅验证SQLAlchemy配置和存储值，不替代MySQL CHECK/锁。

SQLGlot30.24.0原型已撤回：官方纯Python wheel792162字节、SHA9488828cc018453b7a3ba01e65d2749c9a731314c14583695163ca1f358203fe，仅安装本岗tmp/vendor。严格token/AST节点白名单、引号/字面量及函数名词法、NOT/一元运算保护后，425组935差分未发现差异，但完整migrations投影303→294只省9，590次解析旧6.61ms/候选88.33ms，约13.4倍。该样本是离线解析诊断，不是请求性能。生产无SQLGlot导入、依赖清单/锁文件未改，9不计入68。

root后续明确放开seed旧digest/精确分布保持：允许设计新VERSION的简洁合成算法，保持外部CLI参数/结果形状、必要规模和完整业务性质。先封稳定68回退点，再分支原型，不将新算法预扣或覆盖旧sealed数据。

## VERSION2候选完成（最终数字以此为准）

稳定68提交5f779388；新分支设计43d8f14、产品精确1076677527bbfc94e376ce1a564fc461622b5dee，均已push。实际seed348→326另22，持久Python1691→1601净90。原计数器对107的完整产品6335→6245，--require-range真实exit1，仍超5100共1145；原始完整source-count、逐文件预算及verification.json均归档。未达到400–500/额外80–120目标，不压格式/改口径。

slot序列统一评审/评估/批准/交付/回滚的时间，保证前驱已实际交付早于后继计划开始；统一证据注解/ID和指针列派生及DAG枚举。默认量/七态/三独立角色及完整JSON与业务代表性保留。VERSION2读取当前及所有已知旧seed marker，旧manifest版本或配置拒绝；不迁移/覆盖旧sealed数据。

原975全部业务性质断言保留，当前按VERSION2选择在性质验证后冻结的两个摘要；V1两个旧golden及935来源另列常量，当前未执行历史V1实现。V2对应小92ea1b.../默认a21004...；旧V1黄金对新算法真实1红已压缩原字节留存。新性质13场景33.10s通过，包含默认6000完整35FK、所有JSON/指针/版本/角色/时间/容量，以及另空库batch127重现。原先2红为新增测试误算只读UoW commit，修正到seed刚返回时立即断言单commit，原失败未删。

最后旧marker读取保护之后，准确107当前源：975+新性质小目标14通过/2未选1.84s；原975默认6000单目标1通过/2未选25.95s。原record_property/JUnit警告保留。13与14/1有重叠和不同源边界，不相加为独立用例总数。12个持久模块所有原函数/方法签名AST相同；specs、backend/migrations及frozenDDL对935净差异为空。最终项目限定Ruff通过。

Issue4已真实COMMENT并按单ID GET全文逐字核对：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6397356591 。没有新PR/设置review通过/触发完整CI。root负责采用稳定68或额外22的版本2取舍、准确集成审核、CI中新tmp812目标和后续freshMySQL。当前仅开发SQLite/mock，真实MySQL约束/并发锁、新版seed native CHECK、完整CI/coverage、独立验收、正式性能、最终规模达标仍未验证。

证据提交1af77aa的完整git diff-check真实exit2：旧黄金真实失败XML含原始pytest的`E`后空格，原字节保留，不修剪证据掩盖提示。同一证据提交仅源/说明文档范围diff-check exit0。完整检查失败不被提交成功覆盖；raw-evidence-diff-check.log和verification.json另记。

为便于根审查最终补丁，原失败XML与原diff-check日志随后仅改为gzip封装，解压字节/SHA256与压缩前完全一致，verification.json记映射；1af77aa和ee8e678的历史检查失败仍保留。没有删除原失败或改其正文。
