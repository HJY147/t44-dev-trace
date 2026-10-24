# 独立验收 v2：受限真实故障阶段

**仍未完成整体验收，不能判总通过。** 精确SUT为`4c20f32b71635016815420472b9d4bb4fa850df0`。本阶段实际执行4个故障子集通过、1个原消息捕获子集BLOCKED，另有fixture SETUP通过；没有确认的本阶段产品缺陷。不得把子集结果当作完整SCANS/MQ/事务验收通过。

本次仅继续原run39969411280中未完成的故障分支；既有API阶段没有重跑。原冻结947/949/950等字节保持，921补充解析真实TSV审计输出、核对实际逐次恢复JSON，并按实际升级关联outbox行识别中性三字段wrapper。原先基于task-id子串的识别被明确替换为实际行关联；未猜未来ID、未制造产品消息或修改产品。H4具有f118环境与H3两个Git父提交；原始冻结/尝试不被覆盖。

| 已执行子项 | 结果 | 实际边界 |
| --- | --- | --- |
| MQ-01-DUPLICATE-SUBSET | BLOCKED | BLOCKED：实际升级/outbox关联已取得，但观察窗口内未安全捕获原队列消息；未执行重复发布后置断言。 |
| SCAN-01-SUBSET | PASS | 20个真实逾期任务，含5个阻塞任务；首次最高级别2、完整收件人快照、各一次版本/升级计数；调度进程stop/recover后等待65秒再扫无重复。未证明中批崩溃/cursor恢复。 |
| MQ-01-SUBSET | PASS | RabbitMQ stop期间20个任务各取得标记fallback的本账号通知；读/处理区分且任务不变；恢复后无重复并保留读/处理；新事件得到非fallback通知。未证明全部收件人实际通知、确认歧义或迟到原消息。 |
| TX-01-RESTART-SUBSET | PASS | 已提交任务开始开发后API stop/recover，任务快照完全一致；前后两条create/transition审计行的取回字节也一致。未证明事务中途、提交ACK丢失或audit-only故障。 |
| TX-01-DBDOWN-SUBSET | PASS | MySQL stop期间已授权读取返回503且audit_id=null，逐次恢复后任务完全一致。不是独立拒绝审计故障。 |

## 逐次恢复与证据

5次显式recover均取得不同recovery_id的真实JSON、schema1、requested/restored服务集合及所需步骤实际退出码；不需要unpause的步骤为needed=false/exit=null，不把null当成功执行。每次恢复完成均实际验证。6服务恢复范围是控制接口的固定恢复集合，**不代表对6服务都实施过故障**。本轮是stop路径；环境自检的pause合成回执不算本产品pause用例通过。

调度重启后等待完整65秒再检查；这只证明所测干净重启/重扫，不是扫描中批游标恢复。MQ降级仅核对该账号的20条fallback通知及读/处理状态，虽事件快照已含完整收件人集合，也不能据此宣称所有收件人的实际投递均已核对。未能捕获原消息不是产品去重失败，未发布或执行其后置断言。

API重启前后的任务快照完全相同；两条实际成功审计记录（创建和开始）也逐字一致。这是已提交记录持久性观察，不是事务原子性、丢失提交确认或独立拒绝审计故障证明。数据库全停时503与null audit_id只反映数据库不可用边界。

## 精确复查绑定

- 环境`f118f9dd35bc2cde69affe235f5a499d03a396fc`；中性白名单commit`6b681dd73694bf18430f1bce4bdf00ffd1ae762e`，manifest SHA256=`362a9914e31bfdc3709a941ca9cb26b199a933f3ca8e1c959d0c9bde86c6f21b`，7文件hash和bytes均独立核对。其environment-check只作能力凭据。
- H4=`2e1917e2e9e1c307bd0fab0ed74ee61de15a71d7`；R5=`4d3033e9d1aeb89f150521ba89e38cf3304e3a25`；run39998518039；入口`tmp/independent/private-v2/921_fault-resume.py`，timeout1200秒、request_revision1。
- 冻结原manifest=`994309f0f394ed42ee01016f6d737de20089c13a72757a459c470e0d29a981e7`；原cases=`1ba304140eb63774dc790c9a1a72eb5ccda76c22a5c5d6181086ea40c03c5ca2`；921=`9207a472c44291a50964233f10ac26be4a008300c3ca5ff47feb75bd0f936b58`；920补充manifest=`1d9d2c6ec66e31d5bb8d17ca5dfc9488407bbbee19d3f4f6531271fca4e81fd2`。
- CMS=`b7ce61a6b659e533ef6f26ba94208d934461f16eaaf65bb38353ab0562507b44`，认证解密成功；本地私钥仍0600未上传。原私密results=`4e12296a5dc3b758fe0e4d734834bf98cd620e0eebc228abdfa92e0d6a096b6a`，events=`6b94eefcd6ff7df87449a4ff94f0c79b9d83d8b9cf4ebca0aa0363e193eec408`。

环境ready、harness确已启动，exit2保留未完成项；finally总体true不替代上述5次逐次证据。原phase_artifact最后值只能代表最后一次赋值， earlier cases以各自事件和断言为依据。所有执行函数/原始错误/未运行项仍保留。

选择性事务barrier、提交确认丢失、audit-only、扫描中批崩溃、完整101收件人/时钟边界等未由这些子集证明。正式400VU性能和白盒/CI/覆盖率等仍未执行，不因发布删减原计划。AC07/AC06整体未完成，其余验收项沿用API阶段明确的边界。

独立tester仅明确发布本文件与`v2-fault-stage-results.json`两份脱敏阶段文件，允许root/开发读取；私密脚本/用例/原日志/解密目录/截图/凭据及密钥仍不公开。此文件不是最终整体验收报告。
