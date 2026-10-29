# Future neutral CAS代码限定审核

## 1. 范围与版本

固定AI审核岗，只与root通信。root已发表原件限`records/cloud/r30window01`：R30为NOT_RUN_PREPARATION_INCOMPLETE、六个准备POST实际409顶层VERSION_CONFLICT，竞争写者未被独立证明；正式QA prepare/grant/execute均未运行。两机经济停机、auto-release `-`、各保留一盘属于root公开回执，本岗未查询云。本次不读取.runtime、QA PRIVATE、REVIEW_R30_ONLY、core或未发表case。

新future目录`agents/backend/neutral-r30-cas`，红基线7936fe2a与初修5635cac1保留；原neutral-r30/manifest66ab、旧实际materials c283及产品0b不修改。最终准确提交`cb966f2117730d6b60227e85e30b6a8b0e3cc79a`，18件manifest `0fc61e463692622f167548b7b00aed42fc18a58a0ae127317d6138e0a6136b8b`已由Git原字节逐项hash/size锁定。

## 2. 必须保留的P1：未来APP executor尚未实现

新prepare_http顶层import escalation_readback，后者需要真实`t44.contracts.violations`和`t44.scheduling.rules.load_rules/select_window`。原HTTP容器为source-free4f，不能导入t44。本岗实际在隔离stdlib+新producer路径执行import，先报No module named t44，未做任何HTTP。root接受此P1，明确未来APP HTTP用已绑定官方backend8e，edge-only、UID10001、readonly/no caps、不注入业务/DB/AMQP env、保留镜像PYTHONPATH；LOAD/QA仍4f source-free，不改旧执行原件。

初审代码目录多了非manifest的verify-local.py，运行目录不能直接满足原wrapper全部.py集合核查，已先报root。最终cb将该入口移tmp756；Git实际九py集合已与18manifest中的九py完全一致，此代码集合问题关闭。未来运行staging仍须只搬manifest18件，不得放宽wrapper或混入测试入口。运行需求说明及runtime-only函数probe不等于实际executor/image/UID/network/staging实现，因此**future execution readiness P1仍开放**，本次不能行政关闭。

## 3. CAS语义与拒绝边界

只捕获HttpRejected且status409、顶层code VERSION_CONFLICT，并用真实冻结Error schema完整校验；其他HTTP/code/嵌套或残缺envelope不进入恢复。原请求ID/status/raw SHA和原envelope继续私密留存。没有把409 current_version/current_state当成功task，也不归因scheduler；每对象仍只发一次原POST，无retry、stop scheduler、变core或改请求门禁。

正常GET rules核原完整snapshot，task→分页events→task核真实同对象/项目/原schedule和plan/合格state/版本前进和稳定关键字段。通过官方rules与select_window核准备时及完整冻结窗口同一level，拒缺事件、旧schedule/wrong rule、错对象、重复current事件和变化快照。采用完整GET原事件，不重写scan_run_id、created_at、recipient_ids、disposition、handled_count；正常POST也须与GET原事件关键身份相同，允许consumer合法后续处理字段保持真实。最终旧guard/evidence仍执行，不以新helper替代完整材料门禁。

## 4. 独立窄检查

本岗`tmp/755_neutral_cas_review_r30/755_http_boundary.py`只用标准库与明确synthetic连接：5种HTTP outcome实际走真实Client.request，保持顶层原envelope/status/rawSHA/requestID/0600且只有一次请求；另隔离import复现runtime P1。初2组检查0.056s/0fail/error/exit0，原件以initial后缀保留；cb新增明确缺包RuntimeError后按最终字节2组复核0.060s/0fail/error/exit0，结果`755_http_boundary.json`。无服务/HTTP/Docker/云/实际session，不伪称真实validator/rules执行已由本岗复跑。当前默认本机python无jsonschema/referencing/pytest，本岗未为此安装或读取.runtime解释器/文件。

## 5. owner原证据与测试独立性

原red XML2cases/2fail保留；首次green42/0fail，原全回归78中1fail也保留；最终cb原XML81cases/0fail/error已核，时间4.33s采用owner原记录，不称本岗重跑。已读公开源码中的合成竞争、正常POST、consumer disposition、分页、其他错误和不稳定对象负例，不访问独立测试用例。本岗独立AST比较原759与迁移756的40条assert完全相同；只有future目录及完整官方rules fake响应的测试迁移；不把合成scheduler race等同六个实际409的竞争写者归因。

## 6. 集成边界

只可由root集成未来准备代码和清晰运行接口；本岗不代集成，不发global reviewer/stage、APPROVE、main保护或SUTgrant。产品0b/原CI/5880仍超780与准备工具分开。服务器保持OFF，无自动新窗口，不重用R30旧session/packet，也不回填其失败或时间。

## 7. 未核内容

未来官方backend8e的实际HTTP executor和18件staging，镜像identity/ordered layers/runtime origin、edge/UID/无业务env实际回执，实际并发写者、完整新API造数、四个新session TTL、新binding/window、独占对象、QA prepare/性能与停机后验均未执行。本地代码/函数probe通过不能替代这些内容。

## 8. 结论状态

**允许root仅集成准确cb966f21及18manifest0fc61e的未来CAS准备代码/运行接口。** 相对原66ab运行清单只修改http_primitives/prepare_http并新增helper，其余15件hash不变；valid_task/create_or_read_existing函数AST在563→cb相同，新增runtime probe明确只验真实包/函数，actual_image_identity_verified_by_probe=false。旧产品/neutral17/运输/部署/specs/frontend/原tests实际diff空。本次代码P2新增0，未来执行P1仍开放，不发BOOT/SUT/global grant，不将future部署记READY，不阻塞历史R30封存。最终绑定原件`755_final_source_review.json`；报告、四件、原prompt及真实命令只在本岗分支维护，技术结论先发root。

### 后发固定runner：代码P1关闭，实际云门禁未执行

上一段及Issue3 COMMENT6494709568是cb交付时的真实状态。随后root派审新r30-http-prepare.py：初14573B/SHA054661的checked要求C=G，与producer G35/C40严格矛盾，本岗即时P1报root；原5mock绿使用错误C=G fixture，不能当跨owner可执行证据。owner保留真实C fixture2ERROR红后修G=t0+2100/C=t0+2400、cutoff=S−150、D780..900/E≤G/C−E≥90。本岗另报原HTTP资源限额遗漏P2，恢复CPU2/1GiB/pids128/tmp32MiB。修改均由部署owner执行，旧c283/产品/guard不改。

最终runner14966B/SHA c2c322bd0c932928fcd811d49a4c92f2b45188d2f32b2669fab79a27df9e4e2e，位于准确提交ac005e1c1b842d5813b6dfefa73885f9a1df44e0；交付HEAD6ae6d291a526c6317d6e950cfca7e100418a15e3无runner源码delta，仅补测试/日志/receipt。固定官方8e alias/actualId与原config证明链兼容Docker29，拒4f/旧run/错scope/过期；清洁host env且不传env/env-file，edge唯一网络、10001/readonly/cap-drop，复用准确8c库核18manifest/九py及原source/bundle。先真实函数runtime probe，再固定HTTP argv；原inputs不改，超时只按自己新UUID/owner/image inspect→stop→inspect，不重试，前缀排他保留。函数probe不声称镜像identity，wrapper另核实际alias/config。

本岗755_runner_boundary.py纯本地直接执行runner与准确cb guard各自真实窗口block（不是完整check_plan或Docker）：合法G35/C40共同接受；C=G、错G、错cutoff、D779、E越G都共同拒绝。固定HTTP argv交cb真实argparse通过，UID/资源/env边界通过。owner最终5mock源码/原log及owned_exit仅自己stop/错owner拒绝补断言已核。原错误C红、首资源test seam ERROR等保留，没有新绿替换历史。

**当前更新：cb966f21+ac005e1c（交付6ae6d291）可由root窄集成，future runtime代码P1及资源P2在准确代码范围关闭。** 实际官方8e容器/平台/UID/edge/无业务env/18staging/真实HTTP、预算/新session/新窗口门禁均未执行，仍CLOUD_UNREADY，没有BOOT/SUT grant或新轮授权。代码缺口关闭与实际平台待验分开记录，不阻塞历史R30封存。
