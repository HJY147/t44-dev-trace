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
