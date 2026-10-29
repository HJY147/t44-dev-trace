# 中性准备程序严格 CAS 读回候选

root公开导出的1385次准备HTTP包含200=1015、201=185、202=179、409=6；六个均内部升级POST，实际顶层code为VERSION_CONFLICT，非error.code。静态原create顺序先CAS version再查同排期/级别已存在事件，因此准备程序早先task列表在正常scheduler合法写后可能过时，原统一ValueError没有只读采用分支。两份PUBLIC材料不含足以证明六任务匹配事件的原GET快照，故只确认失败与根因机制，不宣称六个现在可恢复。准确输入SHA与投影见observed-PUBLIC-summary.json。

新future目录保留原producer17全部历史原件；只改副本http_primitives.py、prepare_http.py，新增escalation_readback.py。HTTP失败异常携带原status/envelope/request ID，requests证据仍保留409失败。仅严格409 VERSION_CONFLICT及完整原Error schema允许只读复核；其他错误原样拒绝。官方Task/EscalationEvent schema及load_rules/select_window核当前/完整窗口等级、同task/project、原schedule_version/plan、当前rule_version与唯一现存事件；task→event→task配对，变化拒绝。POST不重试，不降CAS，不读409 current_version拼任务，不删换对象，不预造通知；consumer正常状态变化如实GET采用。成功核对逐对象0600排他保prefix，外层失败不丢会话/原HTTP记录。

红阶段7936fe2a：2红0绿0.29s，实测原Client丢类型化状态及完整400流程在合成scheduler竞争时失败。修复后完整400/6400口径、60个合成竞争逐字采用原scan_run_id，及错误/缺失/错规则/错排期/错级别/错归属/快照变化拒绝、真实consumer字段采用、模块编译导入/六CLI/原40断言全部通过。最终78项4.23s；Ruff检查/格式、diff检查及原producer17/运输686/旧tmp759与758/产品和冻结目录零diff检查全部exit0。verification.json含真实argv/stdout/stderr/UTC，local-all.log/XML为最终唯一一次结果，不累计42+78。

原40自测仅复制CODE路径并把旧不完整Fake规则GET补为正式完整冻结快照，40个原assert AST完全不改，原测试文件不改；迁移SHA见test-migration.PUBLIC.json。新增负例首次有一个mutation把原state=2再次设2而未形成变化，77绿1红真实日志保留local-all-initial，纠正测试数据为另一合法state，未减弱断言。首轮import排序、fixture重构unused import lint失败保留；验证脚本初缺__main__使原全模块import自测触发嵌套本地pytest，立即Ctrl-C退出130、无遗留子进程，增加main guard后正常完成一次，详verification-interrupted/initial记录。没有把这些失败当通过。

新manifest18运行件，kind/name→sha/file_sizes形状保留；baseline manifest原66ab和执行过686均不变，新helper需要部署owner未来审包。产品source0b及API/DDL/业务/权限/版本/事务/幂等/锁/审计/MQ全部不改；没有新依赖、云/SUT/真实session或额外CI。旧窗口绝不重开/改钟，本候选仅供下一新窗口前审查，不是QA或性能验收。
