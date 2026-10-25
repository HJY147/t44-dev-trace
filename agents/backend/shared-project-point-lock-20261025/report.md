# 项目共享门与逐点任务锁候选

作者、实现与验证执行者：后端 AI。root 明确准入修订路线后，先提交设计勘误 4dc0ca6，再测试 8db9aa8/3f1e355，产品候选 **c8cea7e82805de5283ce67501769fa9a4efc1047**。Runtime SHA-256 **9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b**。仅为代码候选，未合并、未云部署、未证明正式性能。

## 改变与保持

仅产品 Runtime.locked_scope 两处：原 graph_lock 的 START/UNBLOCK/REWORK 分支 project S，原 _PROJECT_LOCK writer project X；原 ids 集合全部路径 sorted 后逐个 scalar 唯一 PK + project predicate、limit1 取 task X，返回值仍丢弃，先锁全体再原 Business 重读。原 S-only+batch 路线未实现，作为历史设计保留，不冒成结果。

verification.json 机械恢复这两个 AST 节点后，整个 Runtime AST 与基线完全相同；ids 构造 AST 也全同。产品目录相对 9286 仅 Runtime 改变；没有 Rows/Business/合同/DDL/鉴权/事务/CAS/错误码/拒绝审计/outbox/幂等修改。锁读缺失或跨项目仍不新增 require，原业务检查负责 404；三个认证点、两UoW及 session→idem→project→members→tasks→children 顺序保持。

每个 scalar ID 都是唯一 PK，原项目 predicate 保留，最多一个匹配目标；不能因 SQL 多ID优化器次序不明而跨请求按不同集合顺序取锁。但这不等于任意业务/故障/外部写者全域无死锁证明，真实 MySQL 锁事实、专审、CI和集成另行准入；不加重试掩盖。

## 真实执行及失败保留

- 首次点锁 fixture 加依赖缺原必需 reason，9 setup errors，未到锁断言。原 log/XML/argv/source 全保留，明确不是9个锁结构失败。同一错误还存在于前阶段未执行的HTTP7图writer输入，现只补两个合成输入 reason，不改契约或断言；旧E按其准确source读取。
- 原 Runtime 上修正fixture后，9个结构目标全部真实失败：实际一个 list-ID 查询，对比要求 scalar逐点；这是真正开发红样本。测试未改，然后最小产品修改。
- C 上原9结构目标加缺失/跨项目HTTP404两项，共 **11 passed/0failure/error/skip**。真实SQLite、原Gateway与原authenticate，检查sessionS/idemX、项目S或X、membersS与后续锁顺序、所有scalar project谓词/limit1、反向ID前驱、body重复去重和原404独立拒审计。不 mock鉴权/Rows/事务；仅当前Gateway.rows临时观察后调用原方法。直接scope结构目标不运行完整领域迁移，不能称MySQL锁测试。
- C 上另 **21 passed/0failure/error/skip** 必要邻接：原859非空依赖、完整交付/回滚/返工、图编辑/删除、认证与幂等/撤销、capacity重校及错误优先，再三条真实顺序fixture。与11不重叠，是本源32个唯一目标。没有重跑56/35诊断矩阵，无本地未知MySQL/负载或新CI/云运行。
- Ruff/format限定三文件通过，现有TestClient弃用warning保留。原始红/绿JUnit、stdout/stderr和实际argv/source见同目录命令JSON。结构红的log/XML包含pytest原始尾空格，首次全staged diff-check真实exit2；现仅这两件无损gzip归档，raw/gzip双hash与逐字roundtrip见artifact-manifest，原文本另保本树ignored runtime，不strip或改失败。初始化阶段两次文件定位 miss和后来工具查找不足均非产品结果；一次宽文件名枚举意外列出旧独立目录路径名，未打开任何其内容，随后定向到已知counter路径，没有独立私件读取/测试岗通信。

## SQL成本与规模实际失败

K=原 target/pred/body predecessor 去重总数，原 Runtime 锁任务 SELECT 为1条，现K条，净增K-1；无前驱/额外body目标时仍1条。当前三个前驱覆盖的结构目标实际四条点锁；SQL账本不能拿无依赖样本的1→1推断全部不增。原985无依赖BLOCK/UNBLOCK SELECT账本预计不改，需root fresh MySQL真实确认；非空依赖账本应按实测K增加，不调整业务/锁断言抵消。

原固定cloc2.10（bf592724…）与原 source_count.py 实际在C执行：**6326 行、within_range=false、exit1**；66应用文件集合与原6316完全同，只有Runtime276→286，净 **+10**，上限5100，超 **1226**。物理diff为13增2删/净11，另1注释不能混为cloc。原统计口径不改；tmp新增167物理行的点锁测试（含空白注释）不是产品精简，原诊断脚本的规模也不冲抵失败。

点锁提供明确顺序但增加网络/编译开销，共享项目门可能只利于不相交请求；净吞吐/P95收益仍须后续真实复测，不能把之前Linux顺序成本或云502指为已修根因。旧云0组600秒、270ms/400客户端/零错和独立验收门槛保持。

## 交接

root/专审审准确C；DB岗已收到Runtime SHA，负责同步逐点查询EXPLAIN、实际SQL/P_S、交叉与共同前驱数据；root唯一编排fresh MySQL HTTP7+DB6race、现有全量CI。HTTP驱动当前SHA **f77f2872fe6dfb8230fec6edb24be5fdcbfe048bf83c4ed319e1a6c7e713caff**（仅本阶段补图writer reason）；其独立空库/环境要求沿前阶段已发布接口。新点锁测试SHA **6f6e14e5442d4b67d204b4200bce2d503ed3792ff2e33c1fdd3e6071c31470ff**。

作者/决策：锁方向与修订方案准入由root依据用户授权和设计审查决定，实际改码与执行均AI；不是用户亲自修改、手测或手写研究报告。原始失败与旧E不回写。当前审核/真实MySQL/全量CI/性能/集成 PENDING；规模实测FAIL。
