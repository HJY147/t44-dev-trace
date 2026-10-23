# 有界本机演示：部署岗设计checkpoint

依据root61b23e6的specs/changes/native-bounded-demo-rfc.md；本岗新分支codex/deployment-bounded-demo从实时root c1aff86建立。旧PR31/34已合并历史、原run1失败/0a6 run2成功及c688→7f/b238→cd3限定关闭均保持，不把新serve视为旧cycle已验证。

本阶段仅设计/工具与合成守卫。新360秒实际运行必须等根确认本机压力比较窗口；新增范围仍需专职审核，用户演示另准入。固定bc5的92源文件、既有锁hash依赖、专属t44_native_demo及原回环端口；不迁移、seed、改业务/规则、读写demo/v2/v3或独立资料。

## 函数输入输出与错误

| 入口 | 输入 | 输出/边界 |
| --- | --- | --- |
| serve --run-dir --duration | 已prepare且未运行过的新自有manifest；真实int秒180..14400 | 单次有界生命周期；时间自serve入口起算，超时/信号触发清理。公共stdout仅脱敏汇总，私密state保存状态/截止/停止说明 |
| BoundedServe控制状态 | duration、单调时钟/UTC、SIGINT/SIGTERM请求 | 校验bool/float/越界拒绝；信号handler只置标记，安全检查点抛受控停止，绝不在任意capture中异步抛出导致子命令泄漏 |
| Application.serve | 新run、bc5精确binding、单run一次owner记录 | 登记runner PID/UID/lstart/PGID/cmdSHA/cwd/controllerSHA；安装/恢复两信号handler；调用原cycle加显式serve hook；任何结局均保留清理事实 |
| Application.serve_hold | 首周期真实就绪、实际项目IDs、当前凭据expiry/session元数据 | API/consumer/UI不重启；必要自有身份/HTTP就绪观察、定时状态；到时/停止/异常退出 |
| scanner受控轮换 | 已知当前session、实际项目scope、TTL300 | 确认旧scanner排空停止→新0600凭据/原子发布→撤销旧→新scanner→持久tick/锁确认；任何失败进入cleanup，不提前记轮换成功 |
| stop --run-dir | 私密serve-owner记录与当前exact runner身份 | 只向完全匹配的runner PID发SIGTERM，不发进程组/全局信号；只说明请求已发，不把它当cleanup完成。runner已退出但无最终清理回执时明确未确认 |

## 默认cycle与停止

保持默认run/cycle原操作顺序和结果语义；serve只显式传入控制状态，在原首周期末进入hold。新增安全检查点只在serve状态存在时生效，默认调用为无操作。首周期包括既有两真实60秒扫描、当前消息事实、原初次受控轮换；hold再执行到期前的额外轮换。已有去重数据只复核真实既有eventIDs，不制造新outbox或重seed。

信号handler只记录第一次SIGINT/TERM及时间，不运行IO、不直接stop子进程。API/UI readiness、扫描/投递轮询及hold在安全点检查；短受限CLI/已拥有broker启动由原超时边界先完成，再进入清理。清理期间后续信号不打断finally；仍逐项核UID/开始时间/PGID/cmd/cwd/source，失配拒绝信号并返回未确认。

duration限制服务阶段；到期立即开始已有有界逐资源清理，实际finished UTC可晚于deadline，必须如实记录，不谎称截止瞬间已全部退出。首周期前停止的汇总capability_ready=false，不称完成两扫描或消息；后置cleanup成功与功能就绪分别报告。

run只可serve一次；排他owner文件/已有角色generation拒绝复用，重启须新prepare。runner的PGID允许与调用终端同组，但stop只发精确PID且核全部指纹，不据此授予进程组信号。私密stop说明保存精确Python/controller/项目/run路径，不含凭据。

## 凭据期限与轮换

沿用TTL300，不延长业务会话。当前scanner凭据剩余120秒即开始轮换，留出stop/真实CLI/重启持久tick的余量；新凭据同两实际project IDs/escalation:write。初始cycle结束先回收控制器自己的ready登录会话并置已回收标记，避免超过5分钟后过期logout污染最终清理；用户自行登录会话不由控制器代撤销。

已明确撤销的本轮旧service IDs仍保留原始签发/撤销原件，但serve的最后cleanup只重复核需要回收的当前会话，避免4小时积累的已撤销会话反复CLI延长停机。若进程崩溃，原issued-sessions全量记录仍可供显式cleanup保守回收。签发、撤销、scanner停机或新tick任一步失败都停止保持，不留下第二scanner/无人管理的过期服务。

## 私密状态与公共汇总

state/serve-owner.json、serve-status.json、serve-stop说明和原始receipts均项目0700目录/0600文件；记录ready/截止/停止阶段/轮换及实际清理。公共结果使用字段白名单，仅精确源/控制器hash、UTC/时限、回环URL/端口、就绪、扫描计数/间隔、消息计数及来源、轮换计数/TTL、停止原因和cleanup布尔/错误码。账户、cookie、bearer、连接串、通知文本、收件人/个人信息和全量嵌套动作不进入公共stdout。

## 必要合成守卫与实际准入

只复用871/873中受影响范围：duration边界、单次run、信号标记及handler恢复、到时进入cleanup、轮换顺序/失败转cleanup、不重启API/UI/consumer、stop身份失配不发信号、请求不等于完成、公共白名单。Popen/DB/信号/时钟用合成替身，不读真实凭据、不跑服务或全旧cycle。

工具commit/守卫绿后向根报告精确source/hash与入口；360秒实际保持/额外轮换/到期全停另等窗口准入，原失败保留；专职新范围审后才另准入用户不超过4小时演示。资源后增能力不回填独立正式三组同次unknown或任何性能/验收结论。

## 唯一360秒后停机检查勘误（先设计，后窄修）

原4ef57b6/SHA942354…的360秒实际退出1、cleanup=false已先封存f1598b9；应用和broker逐项stop=true并不能覆盖post_stop_processes=false。旧verify_stopped把state中一切含pid的JSON都作为需消失的资源，新serve-owner.json记录的runner在写最终结果时当然仍活着，于是唯一self PID被等10秒并误判失败。外部driver随后wait得到真实exit1、独立后置absence为真，二者均不回写原清理结果。

verify_stopped的输入收窄为控制器spawn生成的api/consumer/scanner/ui角色generation记录（保留所有代，不只current指针），以及既有api-children.json内workers/tracker显式子进程清单。role必须为四个已知值且含pid；runner元数据不是这些应用资源。输出仍是逐PID身份观察及all-absent布尔，原UID/开始时间/PGID/cmd/cwd检查、10秒上限、失配拒绝与无信号语义保持。不得用忽略所有活PID或仅检查当前代的方式绕过真正残留。

runner退出由进程外的driver wait确认，并记录真实返回码/时间；内部verify_stopped不可能证明写此回执的自身已经退出。stop入口仍仅报告请求已发与已落盘清理事实，不能在runner仍活着时承诺其已退出；本次不扩展该入口或新增功能。

必要合成只在现有871/ServeGuards增加三边界：live runner元数据+各角色全部代已退出应通过（同例先在原942上真红）；任一真实旧代/当前代仍活着仍失败；任一API worker/tracker仍活着仍失败。own/时钟/等待均替身，强制未调用OS信号，不读取真实凭据或启动进程/服务。红绿使用同一断言，原360 raw不改。新修复仅获得这些合成证据，未获第二360或4h准入，随后交根安排新增范围专审。

原360保护基线的证据范围仅5173/18080/5175/18084/5176/18089/13306；它未包含当前v3监听5177/18086，不能宣称v3过去全时不变。退役18089或可能为空的5176不替代v3证明。根后来指出此覆盖缺口，本岗只离线记录，不补读独立应用数据/端口；下一次如另获实跑准入，必须在启动前纳入5177/18086监听PID/UID/start/argv hash基线并在结束比较。
