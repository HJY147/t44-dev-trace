# 后端架构与规模技术审计（2026-10-29）

审计基线为 `356f29983c904e949245aedfad464efc1bf7b63d`；本报告属于后端/审核职责的技术审计，不是独立验收。仅在独立 worktree 调查，未改共享候选、生产代码、计数脚本、契约、DDL或测试断言，未创建云资源。

原始计数命令：

```text
python3 scripts/metrics/source_count.py --cloc /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/cloc-2.10.pl --output audit-baseline.json
```

实测完整 application 为 **5817 行、65 文件**，固定3500–5100全量口径仍为未达，超717；完整JSON见 `agents/backend/size-architecture-20261029/source-count.json`。源码中的旧留存报告曾给出 migrations 370，实际属于9b0ef6前态；已纠正为本次307，既有SQLGlot CHECK替换收益不得再算一次。

总协调随后传达用户调整后的范围：停止压缩完整总量，按主要运行代码与独立辅助工具如实分组；分组不是修改原计数结果，也不是原全量门槛通过。

| 分组 | 文件 | 有效行 | 说明 |
| --- | ---: | ---: | --- |
| 核心运行 | 62 | 5037 | 原application去除下列三个独立辅助入口/工具文件 |
| 管理CLI | 1 | 147 | backend/t44/cli.py |
| 迁移及结构核验 | 1 | 307 | backend/t44/persistence/migrations.py |
| 合成种子 | 1 | 326 | backend/t44/persistence/seed.py |
| 完整application | 65 | 5817 | 原计数保留，辅助合计780 |

新分组的计算见 `agents/backend/size-architecture-20261029/group-summary.json`。核心内仍保留SQLAlchemy元数据、事务/UoW、会话、幂等、拒绝审计、安全边界、规则解释、调度、MQ和完整前端。辅助项仍随项目交付，未移动、删除或隐藏。

关于原严格全量目标，本轮未找到可可信承诺额外减少717行的架构路径。主要结构已集中：schema.py从冻结DDL派生；通用CRUD、分页、模型映射和契约枚举复用已存在；CLI解析器仅26物理行，Settings总计38有效行；rules.py已复用冻结EscalationRule，剩余严格整数、level/priority唯一性、窗口和UTC检查属于行为边界。不能用删除这些守卫或重复计算旧改动来承诺达标。

最大的探索方向是把迁移中的Inspector签名与原生catalog核验统一为DDL AST catalog，但RowsGateway仍依赖现有schema.py元数据，不能把该文件106行全部计作收益。既有952 owner PoC的解析辅助抽取草图为117有效行，尚缺真实SHOW CREATE正规化、可见性/ENFORCED、catalog缺行及失败闭合等适配；这不是可交付替换，也未证明净收益。试跑因缺sqlglot失败；隔离依赖安装因证书/代理失败，未继续绕过。用户范围调整后立即停止探索。

本报告仅证明本次源码计数、分组及架构检查；没有新增业务测试、独立验收或云性能结论。此前796后端/89前端结果由总协调另持证据，本报告不扩张其范围。实际提示词来源为 `internal-task:/root/backend_size_architecture`，未代写学生研究正文、个人观点或人工经历。
