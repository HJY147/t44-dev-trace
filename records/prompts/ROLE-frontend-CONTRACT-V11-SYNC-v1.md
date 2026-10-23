# ROLE-frontend-CONTRACT-V11-SYNC-v1 实际派工

派工者root AI，执行frontend AI；没有用户亲改代码。本轮不修改共享prompt ledger，仅通知根登记。

## 实际原文

ROLE-frontend-CONTRACT-V11-SYNC-v1：正式续派，仅同步D005/D006显式1.1契约的前端fixture/文档，不做新业务功能。根最终待freeze合同59daa2c6caecbe2f5fe968630dd8eca2fa70fd8e，权威hash a77a5cd635b8f6a9927b60f9befac017055442504e34a95b40eddda809e2782f，info.version与Meta.contract_version.const均1.1.0，38ops/31paths/130schemas无新增operation；根正在等待审核生成新parentfreeze，原1.0保留。前端直接import权威，检查tmp/frontend/981_fixtures.ts中meta版本从旧1.0同步（建议取authority版本而非再硬编码）；不要全局替换review/template其它1.0字段。README当前版本说明同步，保留f654的27CI和80真实HTTP旧cutoff不倒改。只运行与fixture/合同同步必要检查，不开Chrome/服务/新真实browser流程，原断言不降；如本次精确CI已覆盖不用重复全套。自己worktree先合根，不碰BE未提交草稿/测试私有路径，责任内日志/module/handoff/实际prompt/Issue2＋PR14对接、选择性commit后push，并交准确SHA/测试结果。若涉及共享prompt ledger只通知根，勿并改。

## 执行对应与改进理由

安全快进至指定59daa，核对哈希和1.1.0/38/31/130；前端已直接import权威，不添加业务判断。fixture只将meta.contract_version改为authority.info.version，现有982测试增加与Meta.const一致断言，先复现旧硬编码失败再修。README明确1.1同步范围和1.0历史证据cutoff。只检查客户端7项与类型，不启服务/Chrome，不把1.0 CI/HTTP倒改为1.1。冻结父链由root发布，不在本岗宣布。

## 正式父链续指令原文

新1.1正式freeze已到189dc4a3196be0fb84b753f23284f2566d823ea0；14文件hash/18review输入一致，API仍a77a5cd6。你现行fixture/文档小同步不改冻结文件，请对该freeze工作即可。生产新后端守卫才刚准入实现，不能把原f654实浏览器当1.1实现验收。
