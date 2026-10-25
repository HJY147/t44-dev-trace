# 新轮次部署准备结果

部署AI，2026-10-25。最新工具源为`a4055d1f01883c6e969f746ebe6b432f248c9942`，设计先提交`17c1f8e`，首个实现`6124ba2`。本阶段完成的是新轮次工具的可审物化与操作方案；没有云部署、数据库连接、资源购买、账号权限动作或正式性能运行。

`deployment/round-prepare.py`从固定ade5e4c的七个公开模板blob生成新副本；原脚本及10月24日期限未变。新计划声明source、唯一round/project/DB/私有目录、UTC部署/采样/回收/释放窗口、worker、MySQL连接和本轮预算，逐项保留原模板hash、允许字面差量和最终hash。仍使用严格私网CA+IP、原摘要与lock校验；生产默认Compose未改。输入与输出私有、排他，生成main从未执行。生成器声明15连接/engine，另校选定源engine/settings/compose三件与ade5逐字一致；这不是所有模块engine数或运行配置的证明。

W32最少540（可选640），W64最少1020（可选1280），含API、consumer、scheduler及30个operations预留。该算式不是MySQL已分配内存或实际连接数。机器规格、实际worker argv、pool/max_connections、连接峰值、镜像ID/RepoDigests和完整原始资源证据仍需root实际采集。扩大硬件不能记作软件优化收益，也不能解释旧502。费用须root按当次实际报价与累计剩余授权核定，run_budget不是厂商自动封顶。

本地CLI另以合成计划实际物化7件新副本和清单（local-cli.json），退出0、目录0700/文件0600；没有运行任何生成脚本。该计划只供本地检查，不能当实时云准入。

本地合成验证：源`a4055d1`的22个唯一边界检查全部通过（`source-final-guards.xml`，0.16秒，0失败/0错误）。覆盖生成AST/Bash语法、原模板不变、精确源/时间/预算/连接门禁、worker/maxconn overlay及原安全字段、私有文件与排他写入、三件源假设变化拒绝。只对生成TLS的纯定义调用render_overlay；未执行其main，没有Docker、SQL、HTTP、proc或云访问。这不是独立测试或真实运行证明。

此前core6124的18项分别0.152秒和修正loop绑定后0.143秒，同一组不累计为36；源假设增加后4项0.023秒，最终全22项0.16秒。初版Ruff出现两个B023闭包未绑定循环变量，已记录观察、以默认参数逐轮绑定并修复；原未提交/未格式化的逐字源码未保存，不伪造原文件或原始完整stderr。最终Ruff0.17.2 check与format检查通过，diff-check通过。续接检查时系统python与主树.venv缺少ruff/pytest，命令退出1，随后使用已有缓存Ruff及uv --offline缓存环境成功；未安装项目依赖或改变生产环境。一次路径查找给不存在的`.github/workflows/ci.yml`返回rg错误，非产品测试失败。

交接边界：旧fixture launcher绑定旧receiver、worker、source和expiry，未复制到新包；fresh独立实例只向root提供公开recipient材料，再由后端责任岗和审核岗绑定新worker/admin。没有读取tmp829/839/841/852的独立私有材料，没有与独立tester沟通。资源采样新增非原子UTC/perf/monotonic anchor；跨机时钟误差、请求对齐和故障归因仍待实际观察。原始采样按显式完成路径+SHA打包，每机单文件走官方云助手下载；释放和账单分别核验。

实际提示词及AI决策在`agents/deployment/prompts/ROLE-deployment-CONTINUATION-20261025-v1.md`；由部署AI写设计、代码、合成测试、调试和过程记录，未记为学生亲写。学生本人研究报告仍由学生本人完成。该阶段未启动hosted CI；后续集成、实际部署、独立验收、400客户端/600秒/P95≤270ms/吞吐≥1000每分钟以及代码规模门槛均未由本结果判通过。

阶段分支已推送，Issue7 https://github.com/HJY147/t44-dev-trace/issues/7#issuecomment-6394509470 的精确ID完整GET与发布正文逐字相同。该GitHub动作仅模块协作，没有发起云或产品CI执行。
