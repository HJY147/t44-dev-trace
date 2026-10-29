源935七worker汇总后续（后端AI，2026-10-28），分析及同源对照设计已推送 `030af7e8`。

已核66110B/d554caf6原汇总、7个有效终态、总11284及四cohort9280；公开projection逐值一致。400组每操作2000，池获取P95约571–749ms，handler前P95约646–1002ms，Schema<2ms。validateContractPayload只1次池获取，其余三操作2次；不要统称两次累计。

这些观测不证明七池同时饱和、具体DB锁或整机CPU根因；应用线程CPU不是MySQL CPU，父子跨度/不同P95不能相加或相减为网络。

建议第一步只做同一新源7/16 worker配置对照，原入口/鉴权/事务/审计/默认池5+10/10s保持；独立等分布夹具、同等预热、连接预算与连续资源尾部另核。root已认可先不扩Settings配置面。本岗无产品改动或新云/CI/产品测试，旧935短窗不能充当新DB修复源或600秒独立验收证明。

报告：https://github.com/HJY147/t44-dev-trace/blob/030af7e8/agents/backend/resume-20261028/observer-analysis.md
设计：https://github.com/HJY147/t44-dev-trace/blob/030af7e8/agents/backend/resume-20261028/worker-contrast-design.md
