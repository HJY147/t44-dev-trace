# M12 源码准入与测量边界末次附注

2026-10-24，总协调AI编写。它是公开技术过程素材，不是学生本人研究报告。M10/M11按各自固定截止保留，本页另记其后的实际结论。

| 对象 | 准确源与现状 | 可以证明的范围 |
| --- | --- | --- |
| 开发集成源码 | b66fa36a317145afec350d7f61ca374959b2eaf7 的一行依赖查询项目谓词已准入 | 合法冻结库复合FK、授权项目与全局任务PK下读集及id排序相同；pool仍5+10 |
| 新开发CI | product40047832510、Docker40047836840全部成功 | 510后端、89前端；44Python全源/排除0，行2638/2957；20TS/Vue行364/390；容器恢复19表count/checksum相等 |
| 当前完整演示 | bc5aef9c62393134582affb7a690acb33ac2b833，5178→18088 | 不替换正在运行的目录，计划北京时间11:49:43结束；最终停止与清理尚未发生 |
| 四份技术Word | 三份M6、测试M7，共35页 | 复用原已QA文件，截止以各自manifest为准；没有把后来的C或H2校准倒填进旧稿 |
| 未准入池候选 | db87d30449356f3473b645a5c246dcc6c21d7cbe | 保留分支，H2无有效排名依据，不随查询优化合入 |

准入前已在dde39aa1c3ccf122caff5c24584ab69537d09007写明条件。准确C完整CI及公开证据由专审岗18b0271f17fe5c1bcd0453009498028fe14f7a3d有限审核，PR42只发COMMENT并完整GET；AI COMMENT不等于人的APPROVE。总协调另作[准入记录](../../records/decisions/dependency-query-development-admission.json)，含实际集成快照及明确runtime/test/config根与C的Git空diff核对。旧74a样式失败未改写，18旧绿/18新绿是兼容回归，不是bug红绿；没有额外证实“非空前驱全部交付后依赖任务成功开始”场景。

[H2公开摘要](../acceptance/v4-performance-h2-public-summary.md)的六组运行均exit1；有效400并发未建立，产品性能INCONCLUSIVE、不排名，5份环境恢复成功、1份application-ready失败。866正式升级目标请求数为0，不能用准备阶段P95替代；867 oracle/聚合问题及868超时后ACK未知均如实保留。原v3三组正式P95失败仍保留，不能凭H2工具问题追溯改成通过。

[一次本机固定响应校准](../acceptance/v4-driver-calibration-public-summary.md)已完成：3810条client记录、父进程33.410秒，两个自有进程正常回收，无SUT或新正式CI请求。400逻辑用户即时响应也观察到数秒client循环延迟/超时。它证明本机测试路径有局限，不能推断原LinuxCI同因、SUT根因或候选收益。3073个stub解析/回复与3810条client调用计数差异、完整传递依赖清单没有正确事前冻结的问题都保留。总协调仅复制两份明确发表摘要并核SHA，没有合并测试岗分支或访问私密用例/工具/trace。

固定cloc6307行仍超5100上限1207，require-range退出1；F08同时错误优先级未定、精确故障切点/细项错误矩阵等独立证据缺口、学生本人最终研究正文及真实12/5/3人工证据均未完成或未证实。main与全局reviewer/stage不放行，整体NOT_ACCEPTED_INCOMPLETE。

本轮审阅包将按准确源码快照新建，旧包不覆盖；实际路径、SHA及核验结果以外置records/validation/coursework-review-final.json及对应postcheck为准。包内是四份固定技术Word、公开研究素材及内层源码ZIP，不包含本人最终研究报告、R002原话、演示凭据或私密测试。源码ZIP保留M8–M12后发资料；外层少量MD的相对链接需在内层源码目录阅读。不是最终作业提交或验收通过。

生成后补记（2026-10-24 01:26UTC）：上述“将建”是源码快照捕获前的真实状态。现已按4833be05807df5a9d43176eb2ec5a610c7ac06b1新建本机私密审阅包，18外层成员，内层3745源码文件；四Word原字节不变、旧ZIP不覆盖。准确路径/SHA见外置coursework-review-final.json；root另重新打开内外ZIP核CRC、全部成员SHA/可信Git blob/mode及actual ZipInfo常规文件权限，四封面字面值在公开源码及非Word素材中0命中（803份公开gzip额外解压检查；不是全面秘密扫描或OCR）。这两份生成回执发生在源码快照之后，作为外置补记，不声称它们已经包含在该内层快照；外层manifest与审阅说明自带准确源与未达标清单。没有重新渲染/视觉QA旧Word，也没有改写任何测试结论或未来清理结果。

生成后独立审核补记（01:29UTC）：审核岗0735b9d在不读Word正文/独立私密材料、不修改根输出的条件下，对两ZIP及两旁manifest、全部3745个公开Git源码字节、CRC/实际ZipInfo权限和四Word固定hash作有限复核，未见新增实质完整性问题。[实际包报告](../reviews/21-4833be05807df5a9d43176eb2ec5a610c7ac06b1-actual-bundle.md)为生成后的外部证据，不在原T包内；它也不证明课程或整体指标通过。
