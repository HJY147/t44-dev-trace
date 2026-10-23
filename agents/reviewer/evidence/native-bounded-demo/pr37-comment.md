Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-NATIVE-BOUNDED-DEMO-v1
Review target/code: 62ac2f327e7523ffed69a2bd9f98c87ba2372931
Prior design: c19146c002cab7a884be8e5d27794da26d685463
Controller SHA256: 08461886f631e070b206d1533be8be320a90eeea27a0f813795d970f7d9a1e25
Evidence tail: 16b6887cc16500f88134c9482283b4eafc653a37 (same code; not another360)
Original360: f1598b91b710ca897cffcc81c52f2e3a79a33cbd / implementation4ef57b6129c712c1fad88de56775c53b84009b15 / SHA942354aec3dc18eb2518a565fc23d3ae51d8975ac7a4b2d6d497ea1c8dbe3c07
Application SUT remains bc5aef9c62393134582affb7a690acb33ac2b833.

仅源码差量限定关闭 P2 SERVE-CLEANUP-SCOPE-01。新增serve/stop/TTL轮换/owner/信号/时限/清理的所列有限静态范围未发现其他已证实P1/P2或新增实质阻断；不构成新实际360/4h验证或整体放行。

本岗先在e30112a冻结无OS最小输入：api generation101及APIchild102/103全absent、runner777仍alive，期望只核受管子进程而成功。原acdf方法一次真实断言红exit1（查询含777，模拟到10秒）；先于fix读取封档c1f03c1/37-f159原不通过报告。对62ac仅换TARGET和结果JSON名，同fixture/Path/own/time/断言一次exit0，查询[101,102,103]且runner777未查；0真实服务/OS信号/HTTP/SQL/私密IO，无真实等待。

新代码只在verify_stopped将state含pid记录限制为api/consumer/scanner/ui四role，保留全部旧/当前代，API workers/tracker显式清单和完整身份/cwd/leader/10秒/无信号语义保持；不夸大为新增generation文件名真实性校验。整个module除该方法外AST同942，capture/runtime/原测试方法及14冻结不动。owner同案1红→3方法绿，含8role代和5APIchild活残留仍拒绝的source/guard/log原件核实，未由本岗重跑；原工具17绿也不冒称本岗运行。

serve本身的明确180..14400真实int时限、单调deadline/安全点/handler恢复、当前controller与新run、stop完整runner指纹+单PID而非group、请求不等完成、剩120秒TTL300只换scanner及失败cleanup、ready与cleanup分开/公开白名单已作有限静态核对。默认run无serve控制，原完整cycle没有被重跑。未读221私密载荷/dump或独立未发布材料，也不取实际凭据重扫。

原4ef唯一360真实driver1/summaryfalse/cleanupfalse不能因新guard绿改写。原ready、首扫描间隔60.292813秒、额外轮换1次和外部wait后全停单列；controller核4条与owner DB8条扫描分开，无新outbox，16event/26notice为旧链复核。f159的capability/原stdoutgzip在62ac/16b同字节。旧保护基线只核5173/18080/5175/18084/5176/18089/13306七项，缺5177/18086，不能推断过去v3已全时受保护；公开coverage-note保留该缺口，下次须root另准入并补前后PID/UID/start/argv hash基线。本岗未查独立端口/数据。

[原f159不通过报告](https://github.com/HJY147/t44-dev-trace/blob/26b6cf1/reports/reviews/37-f1598b91b710ca897cffcc81c52f2e3a79a33cbd.md)
[精确62ac限定报告](https://github.com/HJY147/t44-dev-trace/blob/26b6cf1/reports/reviews/37-62ac2f327e7523ffed69a2bd9f98c87ba2372931.md)
[冻结及原红](https://github.com/HJY147/t44-dev-trace/blob/26b6cf1/agents/reviewer/evidence/native-bounded-demo/initial-cleanup-scope-probe.json)
[同例一次绿](https://github.com/HJY147/t44-dev-trace/blob/26b6cf1/agents/reviewer/evidence/native-bounded-demo/fixed-cleanup-scope-probe.json)
[新源有限静态核对](https://github.com/HJY147/t44-dev-trace/blob/26b6cf1/agents/reviewer/evidence/native-bounded-demo/fixed-static-audit.json)

仅COMMENT、不APPROVE、不发global reviewer/stage成功、不合main、不自动关Issue或授予新360/4h/用户演示。后续实际窗口由root决定；全局独立/性能/规模/人工提交物门槛不获本轮放行。
