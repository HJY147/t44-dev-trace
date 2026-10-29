# D008实施checkpoint（精确C，完整CI待归档）

后端AI从已冻结d5307551d6b467f84e8254abd0245cdf22bc0a70建独立树backend-release-error-priority/分支codex/backend-release-error-priority-implementation。先计划9bab3cc及v1.2 manifest/15hash核对，再写root分配856、跑旧逻辑红，后改生产。业务由用户D008选择，非用户亲改代码；原F08/1.1失败及未执行尾部不回写。

准确产品C=0dfb55c2191200d947c5423fd9ee74bb0812cc5a，DraftPR43固定。唯一生产修改Workflow原批准引用require的错误参数：评估cycle及schedule均匹配才选APPROVAL，否则BASELINE；原require predicate/位置、SQL/role/domain/CAS/锁/审计/outbox/幂等完全不动。匹配引用不抛该错误，后续domain次序保持。15冻结/DB/DDL/pool/MQ/scheduler/front未改，旧986/859字节不改。

856同一test SHA在旧逻辑3红8绿→新11绿；3红均实际APPROVAL对新BASELINE期望，断言前已核六类业务表完整快照不变、恰一独立拒绝audit/正确request_id及稳定reason23/24。真实schedule重新排期撤销原批准是API流程；cycle mismatch及4项引用匹配但state/role/review/baseline异常是**明确controlled SQLite历史边界fixture**，不称真实rework/实际旧库观测。

11项包括新有效评估+另一合规审核人批准→经理发布成功，随后成功重放保留data/原audit、当前request/server_time/contract1.2及original_request_id；错误COMPLETE先实际APPROVAL、改期后原key仍旧error/status/audit且当前request_id，无outerMeta/无新增业务或audit，新key新版本才应用BASELINE。还有仅批准失效、task/request版本、跨task/missing评估和匹配引用的原domain顺序。未额外注入5xx/owner错误/audit失败，这些不在本次新证明范围；原缓存保证仍以R2和冻结描述为准。

另仅跑4个既有986相邻参数化目标（发布回滚返工、新评估双分支、退评审与改期失效），4pass，不重复11项。Ruff/format这两文件通过，现有TestClient弃用warning保留。本机仅内存TestClient，不起端口、不访问外部MySQL/Rabbit或受保护服务/DB，不读独立资料。全部新回归不是独立验收/性能或全后端覆盖率。

旧失败pytest长trace展开12个内存合成session：精确log/XML原件移本岗ignored runtime0600，仅公件替换session值，原/公SHA与替换次数before-redaction.json。失败计数/断言/审计事实不变，原件不上传；随后短trace仅避免参数展开。代码C已含这些公开红绿/命令/hash/静态原件，本后续E补角色与指标，不能倒填。

固定cloc2.10在精确C实际6310/exit1，较已实测B66的6307净+3（Workflow247→250）；freeze base的66个计量源文件与B66逐字同后才作该增量，见metric-delta.json。仍超5100计1210，不改分母/格式/功能凑数。

新product40060857352及Docker PR40060980119已由C正常推送/PR触发，目前终态/原件/覆盖率及actualDocker checkout尚待receipt，不引用旧510/89。只新源专审COMMENT与准确CI/隔离实库结果完成后，由root另决集成；C未合root，本证据分支codex/backend-d008-implementation-evidence不推动PR头。stage完成可先交接释放，后续完整CI原件另封。


## 精确C的新托管结果封档（未重复运行）

product40060857352及Docker40060980119均completed/success、attempt1、APIhead_sha=C。完整JUnit**522**/0failure/error/skip，由本次artifact实际读取，其中856十一项；contract174/integration93/fault19与全量重叠不相加，不把本机11+4当全量。44Python与准确Git集完全相同/excluded0，行2638/2957=89.212039%、分支659/824=79.975728%；rawcombined87.199%不是行覆盖率。FE89/0failed/pending、20TSVue与Git相同，行93.33/分支88.09%，不扩为CSS/HTML。

Docker actual checkout f8c04285533ebbbdd1b0e3d4f5a95e43e19bb6d7由官方checkout/gitlog完整SHA证实，父3fa88293dd9ff51a86fe1c054fdf5318b318c3d3+C；APIhead不是checkout。171相关运行roots逐mode/blob/独立内容SHA全同，不泛称整提交同。4workers、scanner16创建/2完成、19表源/恢复counts和checksum matched，18业务226列；第二scanner flock拒绝exit1是唯一预期非零。Docker是隔离Compose开发回归，不是独立验收/负载。

官方五ZIP先核metadata digest再开，18+33选定新原件（旧manifest只作文件名口径）gzip双hash与解压roundtrip均核；原ZIPignored/0600不提交。实际run/jobs/artifacts及checkout/byteproof各在records/ci/40060857352与40060980119；新总结records/validation/composite-D008-0dfb-ci.json。不移植旧C510/89，即使部分覆盖数相同也是本次原件读数。cloc2.10 SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83、C实际6310/exit1净+3仍超1210。

当前专职代码审8659d444…已完成，公开PR43 review5636767886实际GET stateCOMMENTED/commit_id=C（非APPROVE），本岗仅读回。root随后报告已合C至开发集成da2d3084696b8458004f554e75ddca722f88bf5a，main不动；这项集成操作者root，不记本岗执行或学生操作。E只归档，产品C头不动，不更新SUT。正式性能/源码规模/独立验收未由本结果证明；root核原件后另记限定admission。本阶段结束暂停，无新运行。
