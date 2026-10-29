# Final window 限定独立静态复核

## 1. 结论与授权边界

固定AI审核岗，非实现者/独立验收岗。产品5868779e→冻结356f29983c904e949245aedfad464efc1bf7b63d及指定四个新ops工具限定范围，当前没有其他明确启动必修P1；发现的两项ops P1已在下列准确工作字节修复并窄核。允许root参考此结论整合准备代码并自行决定只下载/校验/import，**本岗不发BOOT、actual target、live、测试或备份释放批准**。未启动两VM、服务、Docker、HTTP，不读取QA PRIVATE/cases/log、crypto密钥；不等待云或用户来占岗。

用户后发已放宽完整总行数，以主要代码≤5100为口径。核心62文件5037、CLI147+迁移307+seed326辅助780、全部5817为root原计数分组，本岗未另重算；全量5817及原require-range exit1继续公开，但不列为当前启动阻碍，不将全部5817写成≤5100。

## 2. 准确源、build与ops分别绑定

独立树从root10e8bd813a570951230eefc40abcb2dd03bfa0cd创建，branch codex/reviewer-final-window-20261029；356f→10e8应用路径diff空。backend source-aware最终1b4f30c72beee10da14e0c56a0358a2c2ae16577、18manifest023063c342854c7b2bea107774007fcd89973a4d0ab85f5841db31a6a8cb2a5e逐件hash/size核。

实际CI制品的build Git为63c781692b66bbf75f5bb5eed3eaf95a6eb82235、builder SHA add7d91065ed32779f6d692e153d31c514e2d331c9a326f59131490a33644982、build run40869531724；bundle原SHA1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2。当前ops image helper SHA7d6ea9d8990ef2200ac73e062ade9962035247513ad46a5554114f0596618b9e不同，不能回写旧manifest。其余本次准确ops SHA在751_boundaries.json：runtime-profile92fb77d7、Foperator69bd7b3f、backup677a44f1，另实际依赖timeplan e6005de2/Fproject41cf1a50。它们是owner当前工作树字节，后续提交/变更须新绑定，不冒已提交或已云执行。

## 3. 产品差分：未发现新增P1/P2（仅静态范围）

SQLGlot精确锁30.25.0及两个hash新增，其他依赖锁保留；CHECK先完整词法、单表达式、节点/注释拒绝，再AST正规化标识符/括号/合法charset，无优化器。原_catalog_defects函数AST和四目录SQL不变；DDL/schema/Rows/UoW/seed及两份OpenAPI原字节相同。check_schema内部CLI诊断由type/nullable/default合并column_definition为owner明确披露行为，未误称所有诊断字节不变或HTTP错误变更。

通知批量INSERT仍在原event update锁、原UoW事务内；收件人有序去重/排除既有、缺ledger先拒、异常原UoW rollback。engine的同12设置仍拆URL/连接/池，session初始化AST不变。九列表分派保留path/task前置、原query过滤/分页/序列化；Member/Dependency在同页批量取原关联，未见冻结鉴权/错误优先级更改。缓存只预编译identity锁定的冻结schema，动态schema走原构造及原错误收集；有强引用防id复用，输出仍限前100。CSS只共享等值selector/media声明，hover specificity和响应式范围未见改变，前端逻辑/契约不动。

这些是代码推理和原件差分，不是实际MySQL、并发事务或浏览器复测。root已核native product40869266343的796/89及覆盖率是其先前证据，本岗未重跑完整CI、未以其代全验收或性能结论。

## 4. 新ops发现与修复复核

P1-A：初F operator仍按Fstart+2400/G−15接收动作，与本轮Fmax=min1500/G−Fstart−120不符。已先报root，由owner修同一原timeplan/run/source/G/outer截止绑定，max1500与G前120秒、C/outer余量分别收紧。当前纯fixture合法接受，超过1500及G−120均拒绝。五动作仅scheduler_restart/mq_stop/mq_start/api_restart/api_ready_wait，未知动作不能伪成功；固定argv、原owned容器、实际budget lock/readmit；LOAD→APP仅root搬公开request/response，不依赖共享FS或任意远程shell。

P1-B：派生HTTP遗留旧manifest purpose要求，新18manifest没有purpose，F/P都会stage前拒绝。已先报root，由owner改为新kind/status及source-profile/manifest原件契约。本岗以准确1b4f/023063原18件经过真实derive→原producer_files→实际派生manifest gate，已通过；未给原件补旧purpose。临时本地fixture显式synthetic root_approved仅为代码生成，结束即删除；CI profile原件仍false，未授权实际运行。

## 5. 制品、测量身份和时间门禁

只读允许的官方artifact JSON，94条context逐Git356f原blob bytes/SHA相同，CI60 runtime表完整等于source runtime表；未读125MB tar或声称独立重验全部镜像层。当前import工具保原receipt的真实observed_utc、images_loaded_this_observation(bool)、volumes_modified=false；F后P由新prove-loaded独立观察，同源build不冒actual loaded。

CI Python config3c4d与Docker29期望runtime4f3b分列，原投影ce562绑定。准确1b4f guard纯身份核及实际assemble表达式使用expected_runtime_id，config冒runtime的负例拒绝；PUBLIC adapter15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d和target实际常量同4f，core81e不改。target/批准仍待实际APP/LOAD原件，不用CI/单mock称真云通过。

静态timeplan以实际first boot+3h outer，F/P各自t0/G35/C40，P S20/E33/cutoff17:30，Fmax保G前120s；F后P先停F并独立prove-loaded。报价分组及剩余流量余量明确非账单保证，60元实际支出/外部停机监督仍由root观察。没有两个镜像等于两个服务或并发能力的断言，实际APP7/LOAD和一次性工具资源另核。

## 6. 备份与释放

当前backup已取消全局*private*过滤，明确root批准APP目录/卷、普通文件SHA与私有设置保留；冷备卷先要求所有使用者退出，输出不能在选区之内/之外祖先造成递归。APP仅流式tar→recipient public cert加密，不把明文tar落盘；本岗未读取或运行任何密钥。verify-local代码完整decrypt流hash/bytes、gzip CRC、tar成员/文件hash、原selection与required_files，输出明示NOT_RESTORE_TEST_OR_RELEASE_AUTHORITY。

本岗只复核输出递归纯边界，没有自行做crypto/decrypt、恢复演练、LOAD独立证据备份或云数据核验。**本报告不允许删除VM/卷或释放数据**；完整解密可读不自动等于业务restore通过，仍须用户/root按实际本地备份与后验事实决定。

## 7. 实际核查、失败原件和未核范围

751_boundaries.py exit0：94 Git原件、60 CI表、18新producer、LOAD身份正反、真实派生manifest gate、F三时间case、backup选区边界。751_product_static.json核保护文件/目录SQL AST/同12engine设置/PUBLIC adapter原SHA。只有标准库、Git、公开原件和短本地临时fixture，不运行产品/服务/全CI。自有初次fixture路径写错、随后owner增加timeplan参数导致接口fixture过期的两个非产品失败保留stderr，正确补齐后通过；实现未由reviewer改动。

未核：实际APP Docker29导入/缓存/层内容、当轮actual target、F/P真实会话/HTTP/故障/并发、账单和外部监督、真实备份/restore/停止/释放。runtime-profile新增F extra的代码依赖只做必要静态阅读，其他新派生运维入口没有全量安全审计；任何未列新源码或后发修改需另核，不扩大为global reviewer/stage。

## 8. 交接

只写本岗报告、四件、prompt及tmp751证据，未改owner实现、冻结产品、QA源/用例或原manifest。两新问题实质即时报root，修复按准确字节限定关闭；最终仅静态准备准入/CLOUD_UNREADY，BOOT与实际target后置。没有等待用户或云，不将新规模口径当放宽测试/数据门禁。
