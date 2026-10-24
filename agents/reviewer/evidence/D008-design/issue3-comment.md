Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-D008-DESIGN-v1

限定设计审核，准确RFC `8c3d0d646139e2f85ea487230e7a2f185487402e`：[release-error-priority-rfc.md](https://github.com/HJY147/t44-dev-trace/blob/8c3d0d646139e2f85ea487230e7a2f185487402e/specs/changes/release-error-priority-rfc.md)。对照root6432、D008/U021及technical-scope，最小设计未发现结构性阻断；这是纯设计一致性结论，不是实现准入/代码或整体验收通过。

只改原approval-reference失配失败槽：已解析同task assessment的cycle/schedule stale先BASELINE，否则APPROVAL。请求assessment_version、auth/project/task/version/归属现前置不动；引用匹配走原domain。额外state/role/review同时错时保留现adapter槽相对位置，不把全部guard提前；root已明确此技术范围，无需再问用户。

**重放的具体澄清：不是“只有成功 COMPLETE”。** 当前Runtime.rejection在已有claim、owner_token仍匹配、status1、error.status<500时，独立拒绝audit事务内complete保存错误，事务成功提交后可重放。5xx、无claim、owner失配、audit/提交失败不保证已COMPLETE。建议RFC明确此条件，保留旧status/业务结果/原audit，新key走新规；不要把“原结果”理解为整个HTTP信封字节相同。4xx重放更新request_id、保留原audit；成功信封Meta.request_id/server_time/contract_version按当前运行版本重新生成并保留original_request_id。现错误响应没有outerMeta，不在本轮新增错误Meta或缓存全部失败。

规格/运行OpenAPI与成功outerMeta采用1.2.0的方案一致，innercandidate schema1.0.0不动；先新规格/父指1.1的新freeze再实现，旧1.1 manifest/Word/ZIP/F08历史失败与尾部不回写。当前14份1.1 frozen hash仍同，当前应用尚未改D008。

附带859确有意义：两个不同非空前驱经真实SQLite/TestClient HTTP评审/评估批准/发布；0/2与1/2拒绝且下游/边不变，2/2开工/version+1且边保留。056d应用/规范未改，公开owner仅新859一案+旧986邻接一案=2pass；执行在format-only前、最终AST同而未重跑。不能称511全CI、MySQL锁/性能或独立黑盒通过，本岗未复跑。

[八段十项报告](https://github.com/HJY147/t44-dev-trace/blob/6e2430839c44fa024c1d92f03dd8064a7fe8f807/reports/reviews/D008-design-8c3d0d646139e2f85ea487230e7a2f185487402e.md)；[精确源/guard/版本/859核对](https://github.com/HJY147/t44-dev-trace/blob/6e2430839c44fa024c1d92f03dd8064a7fe8f807/agents/reviewer/evidence/D008-design/static-design-audit.json)。责任岗应将上述重放/封装澄清纳入后续设计/冻结，准确新实现后另审；不自动放行实现。

0测试/SQL/HTTP/SUT/CI/服务，无independent private/cases/raw/858/860读取或tester联系。11/28安排和先报价不是费用授权。无APPROVE/main/globalstage或整体通过。
