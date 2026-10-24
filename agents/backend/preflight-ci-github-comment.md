Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

新实现审查目标为草稿PR29（codex/backend-runtime-plan→codex/integration）：https://github.com/HJY147/t44-dev-trace/pull/29 。旧PR16保留历史head，不能据其COMMENT当作7584代码已绑定。

精确被测源7584cd31f0abfd6727d552b5fef31a9303247d58（产品153b9c8、先行caller勘误5a19f80）在product40012517513四任务全部success。原JUnit437/0failure/0error/0skip；contract139/integration84/fault17各自通过且可重叠。coverage文件集合与Git全43个t44生产文件逐一相同、excluded0：行2558/2878=88.881167%，分支612/778=78.663239%。选定原coverage/JUnit/marker/gate/run gzip及SHA清单在agents/backend/preflight-ci-40012517513，解释preflight-ci-summary.json。

只有A及caller窄修正进入生产；三次实时auth/原SELECT仍在，新写2UoW、完成重放1UoW，主成功原子/拒绝独立事务及旧scanner/claim入口保留。14结构红、A25绿、caller2红、7绿1红及实际两keys限定的CAS增强后2绿原件均保留；修正由AI责任岗/总协调完成，非学生亲自识别/改码。B/C/Issue28没有混入。

精确7584固定cloc6108，within_range=false，A净增6有效行；不能沿用初稿净减1说法。未启动新性能负载、未证明正式400×600/P95目标或独立验收/源码规模通过。后续纯证据提交只记录此产品源链，应用与测试字节保持7584，不冒称其metadata HEAD另有一轮新测试。请求专职限定COMMENT，不能自APPROVE。
