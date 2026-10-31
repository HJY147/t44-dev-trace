# P15中断及用户要求的直接压测入口

操作者为AI。用户已报告两台服务器关机，所有agent已停止远程调用；此后仅本地工作，不自动恢复。正式p15压测没有启动，没有allow=true或正式trigger，不存在新的P95/吞吐验收结果。

停机前真实完成：两原hostkey与64/16CPU核实；长期restrict公钥无expiry且root0600；bcec镜像实际导入，OCI descriptor/config证明保留；PL1三参数runtime+persist及2GiB redo resizeOK；API/web启动且flag1/64worker配置保持；400transition计划经冻结经理PATCH首尾+2天、原800ID及400escalation不变；维护最终139UNBLOCK+261skip/400state2、原800守恒。两个新worker仍未启动（最新已核状态）；fresh material09最后SSH超时，完成情况UNKNOWN，不重用该输出。

用户指出“开机后又准备半天”的问题成立：此前将离线组件齐备描述成可立即发压，没有完成真实启动链路和足够的演练。根因包括错误account文件预案与实际初始化账户不符、OCI descriptor与config同一性误假设、工期门槛随时间失效、封存空间/内存预算未在离线阶段落实到可执行路径。原失败和真实修正保留，不回写成功。

用户后续原始要求：

- “别管那么多，我服务器没钱了，把什么工期时间约束全删了，然后直接压测”
- “压测完马上告诉我停机”
- “我跟你说了就是现在做好准备以后再让我开机，结果开机你又准备半天，我现在直接停机了”
- “已经关机了，你将所有准备做好以后开机不要做任何准备检查，直接开始压测”
- “准备好了告诉我开机”

总协调据此采用新r30directp16单入口。取消测试准备中的工期horizon、逐400资格维护、等待完整扫描、人工准入轮次，不改变生产业务鉴权/工期规则。必要登录、当前Task/event/CAS取数和scheduler凭据更新并入压测程序初始化，400客户端/原60s预热/600s稳态/原测量与后置断言保留。由于用户明确豁免旧完整准入，该轮明确DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE，结果不冒称原全门槛正式验收通过。

本地交付要求：APP单次fast bootstrap（原真实initialized账户、正确gateway8443）、原子scheduler更新和既有服务启动；LOAD原测量core/functional不改，以DIRECT_INPUTS_V1进入execute；公钥CMS自动运输，不复制私钥；14GiB tmpfs及测后28GiB封存真实预算自动纳入入口；Mac单命令协调、无云构建/安装依赖/现场改脚本/人工检查清单，无自动重试或自动VM关机。只有本地完整流程演练和单入口集成完成才通知用户开机。
