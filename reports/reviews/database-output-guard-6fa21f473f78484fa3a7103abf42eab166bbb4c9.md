# 数据库离线诊断输出保护：原 P2 限定闭环

## 1. 对象、身份与范围

固定 AI 审核岗，实际 prompt `ROLE-reviewer-DATABASE-OUTPUT-GUARD-v1`。本次精确 E **6fa21f473f78484fa3a7103abf42eab166bbb4c9**，先行设计 **3981e6d986fb4ca129d0f5953fd104c0a6c0efc4**，源 checkpoint **3fc58d18614c394cc588a16b316cf89c1810ecf1**。工具 SHA256 **7ca4640a74a38068ac4f86c0b6a6bfc876cc5f6ce630300264ca117473b327d3**；836 窄回归源 SHA256 **d0de9ac7e61a13ca0bc0dba0d1579b73b34a684f1a1b6c9a776946cb349a2dfa**。

只复审原 `c4e8c696411975ee6964ef3b2254c8f3937ecb32` 被 **8a767b63b08975cef5a3d7d837c904abdce120f6** 拒绝整合的 `OUTPUT-EXCLUSIVE-01`，不是独立验收或后端 CI 审核。本岗没有修改工具、测试、生产文件或 owner 原始证据；新 worktree/分支 `codex/review-database-output-guard`，初始规则与明确公开源/回执阅读后提交 scope 5125cc8，再机械核验。未读取独立私件或与独立岗通信。

## 2. 需求映射与原拒绝

原需求是离线工具输出不能覆盖已有结果。旧源使用 `exists()` 预检，后面 `write_text(w)` 按路径重开；原审核的零 DB 反例已证明，预检后新建的结果会被覆盖，悬空 symlink 也可绕过预检。原拒绝报告和 19 配方/71 Rows 历史证据均保持，不能用旧绿色矩阵消除文件生命周期缺陷。

此次修复只须关闭该窗口并说明真实保证，不须重跑原矩阵，不涉及查询性能、应用接口、DB 事务/索引/池或业务规则。

## 3. 版本与差量

源码 3fc 只改 838 工具和新增 836 窄回归。相对原 c4e8，`backend/t44`、`frontend/src`、`specs`、`database` 差量为空。838 的 `recipes`、`provenance` 两函数完整原文逐字不变，SOURCE 仍为 **0dfb55c2191200d947c5423fd9ee74bb0812cc5a**，本岗逐项核对 13 个绑定源与 C 相同；SOURCE/E 中 838 与 836 两源逐字相同。

E 明列 16 公开文件 SHA 全匹配；原 c4e8 的 15 个 perf-public-c 证据/旧 prompt 全部逐字相同。原 E 中的旧工具 SHA 仍指历史版本，不被新 E 偷换。机械结果及可复现命令文本见 `agents/reviewer/evidence/database-output-guard/verification.json`、`mechanical-verification.txt`。

## 4. 文件生命周期与失败边界

838 **257–270** 行：无 `O_NOFOLLOW` 先明确拒绝；一次 `os.open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600)` 原子排他创建叶节点，不使用 `O_TRUNC`。普通已有文件、目录、有效/悬空链接，以及 provenance 后、open 前新出现的结果都不会由本次调用截断。父目录创建或 open 失败通过 parser error 退出，不执行 recipe；没有降级到普通 w 打开。

打开成功后只用该 fd 建立文本流。`fdopen` 初始化异常会显式 close 并重抛；已创建的空文件保留，没有自动删文件再重试。**300–309** 行 `with` 负责成功和异常离开时关闭流；receipt 的最终 JSON 只经该固定流写出，不再按路径重开。recipe 的普通 Exception 会记录 failed/error_class，再传播异常，但该失败 JSON 与原异常传播仍依赖序列化、写入和 close 成功；磁盘写失败时没有完整结果/原异常优先/原子替换/持久化保证。这些额外保证不属于本次修复，也未被本报告宣称已验证。

固定 fd 能抵抗叶节点改名后被新 marker 替换：写入继续指向原 inode，替换的 marker 不被改写。它不阻止父目录链接、外部改名、删除路径或同用户改写原 inode，亦不保证路径名称持续可达。这与“不可覆盖另一结果”的有限目标一致，不能描述为整个路径不可变或防御恶意同用户的沙箱。

## 5. 原始执行与本岗必要核验

owner 首次 red 命令因为 basetemp 父目录不存在而产生 **2 setup errors、0 failures**；修环境后，对旧源得到 **2 failures、0 errors**，不能把前一轮 setup error 算缺陷红。旧 race 的公开 JUnit 属性 `main_exit=0 / overwritten=True`，新源为 `main_exit=2 / overwritten=False`；旧 dangling-link 也真实红。原日志/XML保留。

owner 修后公开 JUnit 为 **11 passed、0 failed/error/skipped**，日志保留 **1 条 record_property/xunit2 warning**。静态审过836：每次 main 用零 DB recipe 替代，仍执行提交字节/provenance；导入跟踪断言排除 sqlalchemy/t44/pymysql/sqlite3/httpx/fastapi。覆盖 race、普通文件/目录/两类链接、新结果 flags/0600/close、recipe 异常、改名后固定 inode、fdopen 失败 close、无 NOFOLLOW、缺显式 run。没有由这些测试执行原 SQLite 配方。

本岗只解析这些公开 JUnit、核字节/AST与明确差量，**实际测试执行数 0**；没有重跑上述11例或19配方/71Rows，没有导入/运行工具、产品、DB、HTTP、服务、负载或新 CI。835 测试前缀未使用。

## 6. 检查范围与原失败保持

owner 全量 diff-check exit 2 来自未修改的原始 pytest 失败日志/XML尾空格；首次 shell 仍继续提交 bc98ee8 是真实流程疏漏，owner 后补回执已保留，不能说全量通过。本岗不格式化原件、不重跑全量；机械核对该公开回执字节，并实际对 8 个明列源码/说明路径执行 `git diff --check c4e8…6fa21f -- <paths>`，**exit 0**，命令与完整范围在 `scoped-diff-check.json`。这不是全仓静态门禁成功。

## 7. 十项检查

| 项 | 判定 | 证据与边界 |
|---|---|---|
| 1 身份/版本 | 通过 | 固定 AI 审核；设计、源 checkpoint、E与SHA明确 |
| 2 职责与差量 | 通过 | 未代修；只审输出生命周期，无生产差量 |
| 3 API/契约兼容 | 不适用 | 不改产品接口、错误或业务规则 |
| 4 DB/配方边界 | 通过（限定） | recipes/provenance原文及13源同C；未执行DB |
| 5 叶节点排他 | 原P2闭环 | 原子O_EXCL/NOFOLLOW；不依赖exists预检 |
| 6 固定fd与权限 | 通过（限定） | 0600、无TRUNC、无按路径重开；不保证父路径不可变 |
| 7 异常与资源 | 通过（限定） | fdopen失败close/with清理；不声称磁盘故障时原子JSON |
| 8 回归与原红 | 通过（证据复核） | setup2error、旧2red、修后11green分开；本人0测试 |
| 9 证据与检查 | 通过（限定） | 16新SHA/15旧件/2源/13C核同；限定diff-check0，全量原exit2保持 |
| 10 整合判定 | 无新增实质阻断 | 仅本次原P2修复；root决定整合，不发整体/性能门禁 |

## 8. 结论与后续

对准确 **6fa21f473f78484fa3a7103abf42eab166bbb4c9 / 3fc58d18614c394cc588a16b316cf89c1810ecf1**，**OUTPUT-EXCLUSIVE-01 在叶节点排他创建、固定 fd 写出范围可关闭，未发现新增实质整合阻断**。root 可据此决定本诊断工具修复的限定整合；源或保证变化须重新绑定 SHA 审核。原 c4e8 拒绝仍是准确历史，不回写为当时通过。

这不是19配方/71 Rows对修后工具重跑、MySQL/HTTP/独立验收、性能根因/收益、全 CI、main/global reviewer/stage或项目整体通过；不发布作者自我 APPROVE。Issue4 仅以真实 AI 审核身份 COMMENT，精确目标与后续 GET 回执另封。
