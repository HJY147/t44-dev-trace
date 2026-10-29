# 数据库 R29：固定 DDL 适配候选，实减 11 行，未达到 100–250 目标

数据库 AI 岗，提示词 ROLE-database-SCALE-R29-20261029-v1。基线 f5e0d95ea68af33dfb213ac6e8d6b496527ed7b2；局部产品候选 274e2e6bfa6dfb2d90926773002a1a62808ec060；分支 codex/database-scale-r29。只在本地开发，不整合、不操作云、不联系独立测试岗。

## 实际改变与口径

仅生产 schema.py 改动：同一张表以一个 declarations 序列构造，取消三份临时列表及其分类汇合；在原有 checksum 验证后，按已经冻结的四空格顶层声明边界切分 DDL，替代通用括号深度/引号扫描。

原 source_count.py、固定 cloc 2.10、固定 SHA256 工具核验及已提交 Git 归档方式完全不变。精确基线与候选实测：

| 范围 | 前 | 后 | 净减 |
| --- | ---: | ---: | ---: |
| 应用主口径 | 5898 | 5887 | 11 |
| persistence Python | 1672 | 1661 | 11 |
| schema.py | 117 | 106 | 11 |
| 应用文件数 | 65 | 65 | 0 |

两次 --require-range 都退出 1；候选仍超 5100 上限 787 行。本岗争取 100–250 的目标未达到，不能宣称项目达标。没有搬实现到计数排除区、引入外部库、删测试/功能/守卫或变更统计器。formatter 一度额外收拢两行；采用更准确的 declarations 变量名保持原多行构造，最终不依赖这两行格式收益。

## 保持的边界

原 schema_v1.sql、DDL_SHA256、migrations.py、Rows、UoW、engine、accounts、delivery、scans、seed 及原测试文件 Git 对象逐一保持。迁移状态/校验和、schema 语义、公共接口、错误码、锁序、撤权重验、审计、事务和 40项目/6000任务/9000依赖/15000记录造数规模不变。没有跨岗后端业务修改。确切对象对比在 boundaries.json。

历史 SQL 不是可删除的重复实现：它是已经冻结并由 marker 绑定校验和的历史迁移。现行 CHECK 解析与原生 catalog 审计同样包含真实拒绝条件，不把它们直接移除作为减量。本轮未发现可信的额外 100–250 行重复实现，未把压缩元组、schema 字段声明或事务模板排版算作架构去重。

## 实际验证

- 原 persistence、812 自测、Outbox 980、Scan 990/974 及新增 769 联合：168 passed、43 deselected、3 warnings，28.77s。原有默认6000规模 seed 摘要/幂等/不覆盖及当前V2关系/时序回归均在该组实际执行；它们属于开发模块自测。
- 新增 769 最终独立再跑：41 passed，0.24s。20 个实际 CREATE/ALTER payload 与精确旧源逐项一致；18 表在 MySQL/SQLite 两方言的全部列、DDL 声明和索引编译一致；四种未审文本变更在进入 parser 前由原 checksum 拒绝。两组结果重叠，不相加。
- 原 956/794 和 812 defaults/migration-order 的早期53项通过证据保留；不与最终168累计。Ruff、100列 format-check、schema.py Bandit 通过。
- 原988在没有显式可丢弃测试库配置时实际17 skipped；没有连接真实MySQL、读生产凭据或创建数据库。MySQL方言编译和SQLite回归不等于原生约束、锁或并发验收。
- 完整CI、覆盖率、独立验收、HTTP、云或正式性能：本岗未运行。旧 f7 云测结论与这个局部候选无替代关系。

## 原始失败与限制

首个实际共用列投影候选让 migrations374→377/净增3；原956+794的34项通过也不能把增量叫收益，因此否决，差异归档为 rejected-projection.patch.gz。其首次 cloc 目录命令遗漏 py 扩展筛选而含 SQL；candidate-first-cloc.json 的 SUM 不属于应用口径，377 仅取该文件 py 项，后续采用原 source_count 完整计数。

新增等价测试初稿错误假设19个payload，实际为18 CREATE+2 ALTER=20；首次1 failed/40 passed日志和XML原样保留，更正新增测试后的41通过不覆盖失败。初次Ruff报告新增测试有未使用Path导入，已移除；原测试不改。

这个 parser 明确依赖既有冻结 DDL 的声明缩进，适用范围是原 checksum 已通过的现有文本。新版本DDL必须连同适配器和差分夹具重新审核，不能认为它是通用SQL解析器。SQLAlchemy约束为set，构造时约束遍历顺序可能不同；测试分别核对有序列和完整DDL声明内容。原生MySQL未实测是剩余验收限制。

本候选是否采用由总协调决定；即使采用也只实减11，剩余787仍需其他真实代码改进。证据入口 verification.json、before-cloc.json、after-cloc.json、boundaries.json；日志/XML保留原始警告和失败。
