Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-CAPACITY-AND-CATALOG-v2
Reviewed-SHA: 7c27a5f62cc23db8545a28852ed01322a7e172b4
Scope: original C-P4 + read-only architecture/source-count audit only

原C-P4四类同名语义漏检可限定关闭：原957与ddaa035逐字节相同、未改断言，复验exit0，baseline接受而索引列序/unique、FK目标、CHECK语义变异均拒绝；DB公开live14原件+5源码hash一致，18 owner用例0失败0跳过，四类实际DDL变异拒绝/重复迁移拒绝、逐例恢复接受。执行live者为DB，本岗没有重做真实DDL或seed。原live run1/2失败保留，不扩大为任意DDL等价保证。

整体仍failure/not approved：原固定cloc对当前7c27为5886，超5100上限786；旧stage7=5866不是当前结论。只读已发布独立报告/JSON知其旧e8目标未通过，未跟随任何私有证据路径，本轮未复审后端IAT修复或重跑性能。

架构净删除方案：A删双表示/中转command/Gate及id:version往返约180–280行（高风险，IAT修复诊断后再排）；B把facade._run与ScanStore.start同一事务体收口到transaction-local start_run，保留caller UoW约28–47；C outbox锁/owner/lease推进重复约20–35，保留confirm/consume/fallback不同语义；D成熟MySQL AST仅POC，不计收益；E seed现context/add/pointer已复用，仅0–15，不能重复计既有重构。总208–377尚不足786，不能强凑。旧83 CSS/58 domain barrel已删，不再算收益；不minify、不改口径/分母、不移业务到配置或排除目录、不删必需守卫。

完整八段十项报告 reports/reviews/catalog-capacity-v2-7c27a5f62cc23db8545a28852ed01322a7e172b4.md，本岗分支codex/review-catalog-v2。仅本岗归档；不发success、不重写原e01门禁、不APPROVE/合main。B交调度/DB，C交MQ/DB，A后置，D先POC，E不夸大，修复实现由owner提交后新SHA另审。
