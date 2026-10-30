# P13 / material07 离线准备与现场衔接

本轮产品source90b、原七镜像和已应用索引不变，候选为用户确认的APP原盘ESSD PL1/40GiB/3800IOPS。上次现场已确认MySQL卷位于唯一40G盘，但盘级别是用户控制台证据，不冒称guest读回。

## 用户停机约束

不新增自动关机、倒计时停机、guest shutdown、云stop计划或定时任务。全部工作完成并回收证据后立即通知用户，由用户自行节省停机保留原实例和云盘。准备脚本单调deadline仅约束本次自有编排/子进程，超时保留前缀，不关闭VM。只退休准确owned历史停机timer，不另建新timer。原独立测试时长、运行边界、阈值和全部断言不变。

## 本地与现场边界

本包通过本地字节/语法/防篡改与代码审核不代表已经现场准入。开机后仍必须实际SSH认证、原hostkey、当前授权余量、原容器资源与镜像、当前schema/原800ID/业务总量/角色/状态/升级窗口、真实新会话、TLS与packet五件绑定，以及独立审核/prepare/一次grant。它们不能提前假造。完整扫描的历史单轮耗时有55、181、302秒；可能还需恢复旧scan和等待下一轮，不能承诺开机即发压。

新material=r30materialresume07，maintenance=r30restoretransition07。06全部partial原件保留，不覆盖、删除或直接重跑。正式QA run仍候选r30manualp13，须现场确认runs/results/phase/operator-channel未创建或消费，否则停止并保留事实，不自动换run继任。

## 准备顺序

1. 先验证原LOAD16CPU的SSH和传包，成功再通知用户启动APP64CPU。任何当前IP不复用作已核实事实，SSH必须原主机指纹，授权过期由用户按原USER_ONLY脚本在原实例恢复。
2. 上传本包到全新07目录；使用verify_bundle.py核全部文件及archive精确字节。输入旧STOPPED-PREFIX只作历史完整性证明，不能替代当前probe。
3. 按RUNBOOK.md新07入口执行。当前400仍全state2时省略重复UNBLOCK；如果需要恢复，仍调用原helper并保留全部资格/审计/读回门禁。原material工具所有实际资格验证不减少。
4. 生成鲜活07材料，原子轮换scheduler凭据，观察持久原scheduler完成rotation之后新启动且完整成功的扫描，保留原成功判据。准备扫描等待预算900秒、整条准备单调上界1800秒只约束准备流程；不变更正式测量，也不关机。期限不足或失败保留prefix，不自动重试或创建后继。
5. 独立测试岗只收当前中性原件/密封packet，独立签本轮身份、零SUT prepare和一次许可。所有未签模板始终false，root不代填批准。当前源/schema/资源/会话/输入/排他事实改变则许可失效。
6. 原ENTRY正式一次400客户端、60秒预热、600秒稳态，P95≤270ms、每个测量分钟吞吐≥1000、零业务错误及全部原断言。不得额外AB或磁盘压测。
7. 原执行进程退出、所有证据写入停止后密封workspace，下载cipher+receipt核SHA/bytes，回收APP中性观测。立刻告诉用户可以手动节省停机；独立本地解密/判定不占云开机等待。FINISHED不等于PASS。

原临时授权的寿命是SSH访问权限，不是自动停机时间。当前中性输入、输出路径、recipient证书及精确命令以包内RUNBOOK和qa/qa-intake公开接口为准，不使用旧06启动说明。
