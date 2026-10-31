# Direct16之后：仅本地修复后置测试工具

用户确认继续，服务器已被通知可以停机；不连接服务器，不发新请求，不自动重跑。原Direct16结果不可回写：性能指标PASS、后置不完整整体NP。

已确认：16个后置错误结束于稳态结束后40.004～40.020秒；两个Timeout已有完整HTTP200响应，阻塞位置为后置验证AsyncResult等待截止。之后13断开与1None.close紧随停止/清理，不直接归咎生产接口。原243最终快照/227审计完成/157未观察保持不变。

工具owner以认证raw定位：4863个audit URL全互异，已经按task_id/page过滤，无项目页重复请求；原每进程已有Validator缓存。不得凭猜测用项目级共享替代原任务范围或声称修了不存在的重复编译。候选将原后置Validator语义编译、提高仅post阶段并行并修正in-flight/close/stop次序，保持测量400/60+600和原40s判据、400最终快照与完整审计检查。所有后续速度数字属于本地工具回放，不等于云端补验或修改旧NP。

部署正式入口bootstrap pin已由独占live派生写法同步到正式源cc94，补含中文完整packet的host集成和错误绑定在session前拒绝；不会再次使用旧ASCII-only绑定。旧已消费run与源图均保留，READY仍COMPLETED_NO_REDISPATCH。

下一步为新候选密文/版本、完整本地差分与压力/短deadline/异常回放以及独立工具复核。未授权新云开机、未将性能PASS扩大成全作业通过。需规/设计暂不写；本文件只是AI实际工程留痕。

## 候选迭代与独立性记录

- v1（owner 4165ab9f，集成29116d75）：400大历史离线回放通过不等于所有边界正确。封包检查及全新无历史审核分别复现schema memo临时对象地址复用导致错误接受；公开标为KNOWN_DEFECT，禁止部署。独立报告集成77e36315，未将作者解释传给审核实例。
- v1.1（owner 07698e12，集成4b897a94）：保留schema强引用，另目录冻结。全新独立审查的153检查及5生命周期检查限定通过（342770c5），但作者额外配额延迟负例发现reserve后越过deadline才dispatch；因此整版仍禁止部署。限定审核PASS不能覆盖实际反例，两个事实同时保留。
- v1.2：另目录补实际dispatch前期限门禁及未发送记录/配额释放。六类边界离线检查后冻结，继续由第三个全新无历史审核实例只收中性源码与要求复核；截至本段写入尚无该版独立结论。

以上操作者均为AI角色，不记作学生亲自修改；总协调只收PUBLIC和中性身份元数据，未读PRIVATE源码、原始响应或测试密钥。三个版本的原始失败与源身份保持独立，不重写Direct16旧NP。

## v1.2最终集成结果（仅离线）

owner提交1161a9b7，root集成a3108cf4；全新独立审核27f1afb1，root集成3b4e9c5b，结论OFFLINE_CHECKS_PASS。独立实例先冻结清单，只收中性规范/身份；实际执行7组检查、400线程所有权和8个spawn验证进程合成正负例，未读作者自测。报告在records/qa/posttools-v12-independent-offline-20261031.PUBLIC/REPORT.PUBLIC.md，明确保留Linux现场、400 TLS连接、资源/故障边界未验证。

owner本版大历史8582次dispatch、400快照+400完整审计，27.3188775秒；5092真响应+2400变异差分、10000临时schema寿命、13退出码及6阶段deadline边界通过。成功预算仍40秒，额外30秒仅drain；晚返回不补成功。所有测试均离线内存传输/合成回放，不能代替云端补验或完整失败路径证明。

总协调验证本版22件PUBLIC交付文件SHA、PUBLIC Python及shell语法、独立报告8件产物SHA及git diff --check；产品backend/t44、frontend/src、specs和compose.yaml对被测bcec源无变化。没有重跑无关产品CI，没有SSH、开机或SUT调用。

归档版本的RELEASE保留生成时pending身份，当前集成状态另见posttools-v12-integration-20261031.PUBLIC.json。旧v1/v1.1不能部署；v1.2仅离线检查通过，未授予现场开机或新一轮压测，Direct16整体NP和暂停文档写作仍不变。
