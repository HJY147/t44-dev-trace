# 准确5cc首次CI失败的窄修设计

后端AI；依据官方run40087756354及job120854051910/120854052090原日志，metadata head_sha均绑定5cc856d6fa94b1fdde32605543b53822f9747f00。原ANSI bytes以两gzip保留，raw/gzip SHA和逐字解压核验见raw-manifest.json。首次gh日志读因ANSI保护退出1，显式允许原始转义输出后重取只是只读下载，不是重跑CI。

## 根因与分类

唯一失败函数为原985_mysql_http.py的test_preflight_real_mysql_transaction_and_unchanged_sql_ledger两个参数：block实际(20 SELECT,5 DML,2 control)，旧期望(22,5,2)；unblock实际(22,5,2)，旧期望(24,5,2)。正好是本候选设计明示、三个SQLite结构目标已观测的两个无必要SELECT减少。不是当前证据支持的业务回归、环境断连或独立性能通过/失败的原因。

coverage日志为560pass/2fail；contracts job内contract177pass/2fail、integration91pass/2fail（与全suite及彼此有重叠，不相加冒独立用例数）。源码clear/local36pass均不能覆盖这次原CI failure；不覆盖日志、不重跑旧run。

## 实施的唯一语义差量

只更新原985 expected映射block的SELECT22→20、unblock24→22，并把原“SQL全部未变”的历史注释准确限定为保留preflight鉴权/事务、Workflow按需依赖减少两SELECT。函数/fixture/markers保持；原DML/control精确断言、三次实时auth锁序、2UoW/2acquire/每UoW commit1/rollback0/closed、replayed判断全保留。plan/escalation/replay的计数不动，RC/撤销/独立审计/幂等/未知提交所有其它用例和断言逐字不变。

不改生产代码、DDL/池/锁/输入输出/冻结、270ms/600秒/零错误独立性能门槛；这是一项开发计数期望同步。不会以回退性能优化、放宽为大于等于或删除断言取得绿色。

## 验证与交付

先提交本设计，再两整数/一注释窄改。AST差异白名单只允许此函数expected[block/unblock]的首项，其它节点必须全同；注释另以文本diff核。按原backend Ruff配置检查该文件，collect-only仅收集该函数5个参数（不执行MySQL，不冒回归通过）。不为已绿本地36项重跑；真MySQL原函数与全suite由新候选正常push的新CI执行，不能用SQLite替身或skip当绿。新源码checkpoint先给root/审核，CI全量结论另归档。

原产品source5cc和原run40087756354/失败永久保留；新候选只test文件变化，应用根对5cc必须逐字同。所有操作在自有worktree，不接业务服务/MySQL/云，不读独立资料或给839发消息。
