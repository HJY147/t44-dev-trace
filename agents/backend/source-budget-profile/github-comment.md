Agent-Role: backend / AI
Prompt-Ref: agents/backend/SOURCE-BUDGET-PROFILE-dispatch.md
Refs: #3

本阶段只做N07静态可行性与离线C原型，独立codex/backend-source-budget-profile从cee7a57，生产应用固定bc5aef9c62393134582affb7a690acb33ac2b833。设计先提交84fee74443ea118cbaf9d541a0d642e4e19377d2；工具870提交964f4bb4796c6bcfa546f3ccba157ce2c5b88515后只执行一次，exit0/main墙0.350673s/CPU0.350167s，无HTTP/SQL/服务/浏览器/私密输入或生产修改。

19自有合成样本完整错误数及前100(path,rule,message)相同，未知local ref双侧异常failclosed；570独立iter jobs/3450错误/30引用异常每模式相同，SPEC/输入未变。只支持这些有限样本，不支持全38HTTP等价/线程安全或正式P95结论。原型根evolve派生保持新实例，但共享只读FormatChecker，这个边界明确未作线程证明。

构造CPU累计生产3.670ms、原型0.438ms；iter_errors累计95.267/87.347ms（均570调用，预建成本另列）。构造只占基线这两段3.7094%，在本混合里不占主要比例；单次模式顺序/105错误样本偏重，不能把iter差异当因果或HTTP收益，不重跑调参。原始JSON/相对热点/方法限制见agents/backend/source-budget-profile/{raw.json,summary.json,result.md}。

N07原固定cloc6307/缺1207仍未解决：一页n07-source-budget-one-page.md只把旧C未应用草案-10当静态候选，生产节省0；即便未来10行全部证明/落地仍6297、超1197。ScanStore.start与EscalationFacade._run同14字段组装、通知分页职责重叠尚无净省证明，不把整段/整文件扣掉。具体取舍：不建议为这点CPU/行数立即生产准入C，根收到正式结果后另决定；大架构/课程范围待人回来，不改3500–5100、不移seed/migrations计量根、不删守卫审计或压行。

生产/锁/14冻结/统计脚本均未改，B/C仍未应用。工具首轮静态F401/B023等草稿错误保留；import探针不加载t44/不跑benchmark；没有新全CI或性能/独立验收声明。执行者为AI后端，不冒充学生手改。阶段提交/原始证据会随本分支push，等待根下一步。
