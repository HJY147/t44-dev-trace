# p13 独立正式结论：NP，不接受为通过

唯一运行：r30manualp13 / r30materialresume07 / r30restoretransition07。原工具、400客户端、60秒预热、600秒稳态及全部原断言保持不变，无重试或后继。实际trigger 2026-10-30T17:30:24.753603Z；原ENTRY于17:42:05.905086Z退出，exit=2。结论来自本地原备份和raw核对，不由exit码推断。

## 指标与原判定

|原类别|稳态请求数|原P95及原Metrics复算(ms)|270ms门槛|
|---|---:|---:|---|
|query|124335|1024.798510|未达到|
|transition|248637|1094.086631|未达到|
|contract|124344|1010.615312|未达到|
|escalation|124333|1095.600419|未达到|

原10个完成分钟桶：68896、64851、64348、60466、60491、61442、61237、60807、59767、58944，均≥1000。621649条稳态记录的原请求错误集合为空；全部400客户端均有稳态完成，单客户端1001–1955次。请求按原开始时刻纳入稳态、按完成时刻分桶，跨稳态终点的完成不计入10桶。

从认证raw调用原冻结Metrics复算：四类count/P95、分钟桶、steady failures、客户端最小/最大次数均与原result精确一致。原Metrics对这些保留样本复算为FAIL（CLASS_P95）；原最终工具判定则因CAPACITY_INCOMPLETE为NP。不能把保留样本当已满足全部测量门禁，不能将P95数值直接归因为APP性能。

## 完整cohort与后置断言分列

原full_cohort=true的精确含义：进入后置检查前，单调时钟达到原稳态终点且当时stop未置位。raw原cohort marker核实400/60/600；647个资源采样alive全400，末采样elapsed=659.062120412s。它不代表400个同时HTTP请求，也不包含后置检查、原始记录完整性或总验收通过。

后置final_task_snapshot仅281/400，audit_complete_clients仅265/400；119客户端post_budget_not_observed。保留raw还记录5个postcheck TimeoutError和1个RemoteDisconnected。MQ delivery仍为原NOT_OBSERVED_REQUIRES_SEPARATE_NEUTRAL_EVIDENCE。故原全部后置断言没有完成证据，不能宣称零业务错误覆盖了这些后置请求或宣称功能通过。

## CAPACITY_INCOMPLETE的具体证据与限制

原result.capacity_or_writer_stop和认证raw footer.reason均为CAPACITY_INCOMPLETE。认证raw压缩流完整可解码，但它是authenticated-prefix：实际701765条、2500483333明文字节；footer声明701786条、2500821235明文字节，相差21条/337902字节。压缩字节389816995与footer一致。不能把该prefix宣称为全部原始交换记录；这直接阻止完整原始证据及全部后置断言准入。

总plain/compressed/cipher用量均未触及原10/11/12GiB总限额。原保留证据未给出容量停止的独立细分原因，不能唯一证明首个触发的是哪条原容量/响应完整性分支，也不能编造为8CPU/8GiB不足。原工具没有改动；本岗初次严格核footer计数触发不一致，随后记录该失败事实而非改写原记录或降低门禁。

原LOAD在原8CPU/8GiB/2048pids限制下，采样memory.current峰值550109184字节、pids峰值403、RSS峰值112632KiB；末采样memory.events的max/oom/oom_kill均0，pids.events.max=0，cpu.stat.nr_throttled=0。队列采样最大81，原result记录writer highwater141。采样结束于稳态附近，没有覆盖全部后置时段；这些值不证明任何未采样时段或单响应/单记录边界，也不支持推断APP根因。

## 证据回收与停机边界

原进程退出、W无打开写fd及协调者无额外W写者已确认后，调用原SEAL。cipher和原receipt准确bytes/SHA核对后已立即通知协调者LOAD可由用户手动节省停机；随后未再访问服务器。

本地原verify_backup认证解密、压缩tar流及75文件hash全部通过，与receipt匹配。cipher为1033156012字节，SHA256=7d18e8b9365027bd59187c93696c946d0605260f2718cc65809cdf22a7ed23b5。备份完整性通过与内部raw prefix完整性不足是两件事。原始实现、用例、key、token、wire及结果保留独立PRIVATE，仅本文件和FINAL_CONCLUSION.PUBLIC.json公开。

最终：NP，不接受为正式通过；完整cohort标记为true、保留指标门槛未达到、原容量/证据门禁失败、后置未完整观察，分别如实保留。未运行新测量或降低任何原断言。
