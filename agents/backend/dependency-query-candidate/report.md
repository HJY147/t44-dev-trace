# 依赖边项目谓词候选（仅独立分支）

后端AI设计/实施，非学生手改。先行RFC ed2737d；产品74aeb2a8d2e60e0c972688a3d68422d3d4a16f2b，Draft PR42。基根b40d888应用逐字bc5，不含db87池默认。唯一应用差异：Workflow.transitionTask的task_dependencies读取增加受信project_id，与旧task_id合取；ORDER BY id、投影、所有其它SQL/空IN/权限与版本优先/域守卫/图锁/CAS/audit/outbox/幂等/ACK不明路径不动。没有DDL/索引/冻结/API或测试变更，没有新服务/外部DB/负载。

读集证明依赖**合法冻结数据**：tasks全局PK使task_id唯一对应项目，edge(project,task)复合FK强制与该task同项目；Call.task先核row.project==c.project，Runtime同主事务已锁目标task。故task_id=t的全部合法边均满足新增project=p，包含空集合。对禁约束损坏数据不保证等价，不用候选过滤修历史异常。14冻结hash、精确单行应用diff/原测试和旧pool字节检查见scope-proof.json。

DBowner公共证据5948cf80已通过Issue4索取/全文GET：请求6377741206、公开回应6377715017；原SHOW确认无task_id前导自动键，对照EXPLAIN估9216→1且仍filesort。只是该小夹具计划估算，不是扫描统计、延迟或正式根因/收益。本岗没重跑SQL。完整原文件出处/hash为DB-evidence-source.json。

同一原986的18个SQLite/TestClient业务目标，旧bc5字节18pass（before.xml/log）→准确74a18pass（after.xml/log）；覆盖交付回滚返工/空依赖、非空依赖不满足、环/开发后编辑锁/删除、幂等撤销、严格union及权限/版本/状态/人力错误优先。没有新镜像断言，没把既有HTTP覆盖夸成非空前驱全交付后的额外场景。此为合成SQLite开发自测，不是MySQL FK/锁或独立验收；时间4.47/4.29秒不是性能收益。严格单源Ruff/format通过，TestClient弃用警告原样保留。

固定cloc2.10实际计74a为6307，范围exit1/超1207保留，cloc-command.json/source-count.json是新原件。首scope辅助核对错误地将全部开发工具与较老bc5比，检出任务基底已有870/955变化并CalledProcessError；记录scope-probe-initial-failure.json后改以即时baseb40核测试/tools不变。不是产品/用例失败，没有改断言/口径。

准确74a product40047094732整体failure保留：基底部署864 UP022/871 B007真实失败；backend Ruff/Bandit、full510/0failure/error/skip、marker162/93/19（重叠）、FE89/20文件通过。44Python与Git全同，行2638/2957=89.212%、分支659/824=79.976%、excluded0。Docker40047211444 success，实际checkout d74cfc8（父728c4e8+74a）有官方checkout/gitlog原行，169相关运行roots逐mode/blob/内容hash相同；不泛称整提交相同。五官方ZIP先核digest再读、18+33选定原件双hash及gzip回读。旧汇总records/validation/composite-dependency-query-74a-ci.json不覆盖。初缺merge对象cat-file exit128，fetch准确对象后核父链，非CI/产品失败。

根准入后仅cherry-pick -x部署owner17e7ac5为7748ca6，保留原作者/两处开发测试样式；未merge根其它应用。其原commit带skip-ci，本岗另提交真实source绑定收据正常触发新源CI，固定C=b66fa36a317145afec350d7f61ca374959b2eaf7、DraftPR42头不再动。应用仍74a，旧pool5+10/14冻结不变；C实际新cloc6307/exit1。原18不重复。新product40047832510与Docker40047836840正在跑；最终数据另封，不移植旧绿。证据分支codex/backend-dependency-query-evidence独立维护。

Issue3 6377896107、Issue4问取/原回应已全文GET。PR42正文原文含末尾换行，初本地readback probe错误rstrip导致assert1，第二完整GET与实际正文逐字相同；保留原probe错误，不当PR/产品失败。当前仍候选，根预先dde39门槛/准确源专审待完成；不自动集成/正式性能/独立验收通过。作者/改码后端AI、样式修复部署AI，非学生亲改；无独立资料、外部DB/服务/负载。


## 准确C的终态（后续纯证据，不推动产品头）

product40047832510及Docker40047836840两新run completed success/attempt1，未rerun旧74a。完整JUnit510/0failure/error/skip；contract162/integration93/fault19与全套重叠。44Python覆盖集与Git逐一全同/excluded0，行2638/2957=89.212039%、分支659/824=79.975728%；FE89通过/20TSVue全Git集，行93.33%、分支88.09%，不扩为CSS/HTML。

新Docker actual checkout9b538128cdb711c0bf08f5a2a7b9774e47069201（父dde39aa+C），官方checkout/gitlog完整SHA与result corroborate；169相关roots mode/blob/内容SHA全同。4workers、scanner16created/2completed、19表逐行数/checksum隔离恢复matched、18业务226列，唯一预期非零是第二scanner flock拒绝exit1。新五ZIP先核官方digest再开，18+33原件双hash/roundtrip；旧五ZIP/51原件及失败同样保留，各source不可混。汇总records/validation/composite-dependency-query-b66-ci.json，原汇总不覆盖。

准确C应用与74a相同，证据分支E只报告/日志/原件，未新增本机HTTP/SQL/测试/负载。候选开发CI通过不改变cloc6307/exit1、DB EXPLAIN非收益、专审/根门槛/集成与正式验收尚待的边界。阶段交接后释放，不自主合分支或继续性能。
