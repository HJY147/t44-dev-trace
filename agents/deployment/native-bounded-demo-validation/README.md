# 有界本机演示工具阶段证据

新工作区/分支deployment-bounded-demo，基于实时root c1aff86；先行设计daaccb7。原应用固定bc5，原capture窄修保留；旧PR31/34、原run1失败/0a6 run2成功/cd3仅关闭P2的历史均不改写。

工具新增serve/明确duration180..14400、私密runner/status、SIGINT/TERM标记、安全点与到期cleanup、剩120秒的TTL300 scanner轮换、新tick/锁确认，以及完整身份匹配runner PID的stop请求。默认run入口仍不传serve控制；capture AST与runtime.py不变，无业务/锁/规则差量。

`serve-guards-final.json/.log`仅执行现有871的ServeGuards 17项：时限真假类型/范围、信号handler恢复、单调deadline、早停/错误仍cleanup、单run一次/ready与cleanup分开、固定source/controller/角色拒绝、ready自己的会话回收、stop精确PID/无group/身份失配拒绝、absent不冒充cleanup、轮换顺序/失败不提前完成、expiry余量、公共白名单、默认run分支。初始14项与后扩展17项分别保存，最终口径17项，不累计凑数；Ruff原件通过。

全部身份/信号/HTTP/DB/子进程由合成替身，未读真实凭据、没有真实被测服务或OS信号；未跑旧ApplicationGuards/CaptureGuards/873全套/完整cycle/中性或独立套件。source-scope.json记录新源SHA/路径，CLI帮助只解析参数，不启动应用。

**工具checkpoint当时未准入/未执行360秒实跑；下述实际阶段后来获一次准入。** 等根确认压力比较窗口；实际证据后还需专职新增范围审核，才可另准入用户限时演示。公共结果白名单与私密原回执分别保存，未来实跑的secret扫描另作真实记录，不能把本合成无秘密状态写成已读凭据扫0，也不能回填独立正式三组同次unknown。

## 唯一360秒实际运行：原失败保留

根在DB955压力比较结束/清理后给一次独占窗口；实际4ef57b6运行见actual-admission-start.json。serve-run1-summary.raw.json.gz解压严格等于原公共stdout，serve-run1-original-index.json保留私密原件SHA及external driver实际exit1，serve-run1-capability-and-failure.json为脱敏白名单投影。

原就绪/首两扫描60.292813秒/额外轮换1次/全自有session撤销与原整体success=false、cleanup=false并列。旧verify_stopped包含serve-owner.json中仍活着的runner自己，是唯一post_stop_processes失败；external driver随后wait完成、全部角色/worker/runner/broker PID与新端口后置absence单列，不能倒填原成功。controller verified4条与DB同UTC真实8条completed分开；没有新outbox，旧16event/26通知不是本轮publish。

此后根仅准入原件封档→设计→离线合成红绿的窄修；没有第二360或4h、服务/HTTP/SQL重跑授权。旧受保护监听与92源保持；后续专审及新实际准入仍需根决定。

## self-runner窄修合成证据与保护范围勘误

先行设计c19146c后，self-runner-red为原942源码相同断言真红exit1；self-runner-green在新源只执行3个新增ServeGuards方法，exit0；真实角色全部8个旧/当前代以及4workers+1tracker任一残留仍失败，own/身份/时钟/等待/信号全部替身，没有OS进程动作。红绿guard字节SHA完全相同。Ruff exit0，source-scope证明仅verify_stopped AST改变，capture/runtime/业务不变。

窄修checkpoint当时新源尚未实际360验证，后续根另准入的一次复验见下节。原运行的exit1/cleanupfalse及postabsence始终保持；external driver独立wait证明runner最终退出。本次没有第二360、4h、HTTP/SQL或无关套件。

protected-baseline-coverage-note.json明确旧snapshot只覆盖所列7端口，不含当前v3的5177/18086；不能把旧列表匹配扩大为v3过去全时未变。只离线补说明，未因此读取独立应用数据/端口。下一次若另准入须预先增补准确监听身份基线，当前仍待根安排新增范围专审。

当前待审代码/evidence62ac2f327e7523ffed69a2bd9f98c87ba2372931，源SHA08461886f631e070b206d1533be8be320a90eeea27a0f813795d970f7d9a1e25。GitHub新正文整体替换/Issue7#6376718503/PR37#6376718790均PATCH/POST后重新GET逐字相同，head62ac/drafttrue的实际观察见github-stage-readback-checks.json；之后仅文档/回执末尾commit，最终head另报，运行代码与新候选不混同。该checkpoint交根专职新增范围审核后结束；后续实际复验来自根的新明确准入，见下节。

## 根另准入的唯一新360复验：真实通过并全停

原62ac专审a7bad288仅限定关闭SERVE-CLEANUP-SCOPE-01，同冻结反例一红一绿/无另确认P1P2；根整合1e9a081后另准入一次新fresh360。工具/应用源固定：62ac的application08461886f631e070b206d1533be8be320a90eeea27a0f813795d970f7d9a1e25、runtimea251、应用bc5的92文件，未修改已审controller/runtime/guard。新app_20261023_233238_345882，不复用原失败run/manifest/cookie/vhost。

原serve-run1-*保持exit1/cleanupfalse；新的serve-retest-*独立命名。新serve起点23:32:39.043824Z/deadline23:38:39.043824Z，duration_elapsed请求23:38:39.044609Z，summary结束23:38:41.688950Z；外部driver wait23:38:42.502726Z得到真实exit0，summary/cycle/cleanup均true。就绪/首两新scan60.324684s、额外TTL300轮换1次/新tick/锁，API/consumer/UI各1次、scanner3代、4worker，3自有service凭据/ready会话全撤销。控制器wait_scans验证4条与DB同UTC实际8条completed明确分开，全部冻结rulehash匹配。旧16confirmed/26通知仅复核，本轮新outbox0/不称新publish，专属库仍2项目40任务。

外部driver在freshprepare前→serve前→runner wait后分别观察九端口（旧7加5177/18086），仅listenerPID/UID/start/PGID/commandSHA及地址，无独立应用数据读取；三个时点每端口逐项相同。它只证明本次补充观察，不回写原7端口snapshot，也不是全时连续监控。后置12个登记应用generation/APIworkers/tracker/runner全消失，Rabbit/EPMDgone，新5端口closed，源92逐SHA不变。

serve-retest-summary.raw.json.gz为原公共stdout exact gzip；serve-retest-capability.json白名单投影；serve-retest-original-index.json记录226个私密非秘密原件SHA，秘密/原dump不上传。operational-driver/post是此次实际外部运维脚本原字节，未纳入控制器。后置提取attempt1因rule_hash bytes不能直接JSON真实exit1，原source/failure保留；仅转hex后重新只读提取exit0，不重跑服务，不将它写为原controller失败或隐藏。

此新360结果只给有限本机开发演示能力；4h用户演示仍未准入，独立/性能/云及资源unknown不回填。根收到退出/清理后窗口释放，此后仅离线封档/秘密扫描/GitHub，禁止自行再起服务。

复验含验证逻辑的三份公共可执行副本依根预留号逐字节迁移到 `tmp/deployment/864_native_serve_driver.py`、`863_native_serve_post_attempt1.py`、`862_native_serve_post.py`；SHA及旧公开路径/当时私密执行路径/现归档路径映射见serve-retest-script-path-migration.json。实际运行时的私密路径、argv、hash和原失败均不改写，历史扫描scope仍保留当时路径。仅目录整理，无运行重做。

本次GitHub正文/head13cd/drafttrue及4条新结果/迁移评论均重新GET逐字核对（github-retest-readback-checks.json）；Issue7结果6376963887/迁移6376983708，PR37结果6376964164/迁移6376984017。最后仅文档/回执封档，实际运行工具62ac/084618、运行证据10182、目录迁移13cd分别固定；最终docs HEAD另报，不代表运行代码变化。当前全停，4h用户演示仍待根另准入。

## 一次14400秒用户演示：后台进行中，最终清理未发生

根f1e530e合入新360/目录整理后，明确另准入一次14400秒后台用户演示；固定工具62ac/084618、runtimea251与应用bc5/92源，未采用其他候选源/规则/TTL。fresh app_20261023_234943_3f9bad，新manifest/cookie/vhost；2026-10-23 23:49:43.904838 UTC开始，2026-10-24 03:49:43.904838 UTC（北京时间11:49:43.904838）截止，届时开始自动清理，最终finished可晚于deadline。

user-demo-current-capability.json为初始交接时点白名单：ready、首两新扫描60.319299秒、初始+首次hold额外TTL300轮换/新tick/锁，API/consumer/UI各1次、scanner3代、4workers，旧service回收/ready会话回收。已有16confirmed/26通知仅复核，不称新publish；本长演示未另外查询全量DB扫描/outbox计数，不把wait_scans4条当全部扫描。九端口prepare前→serve前→ready身份逐项相同，仅三个时点，不是后续全时保证。

外部detached driver PID43819，仅新ignored user-demo-20261023目录内复制参数化既有864/862运维编排：14400duration/15000外部等待上界，追加ready身份快照，真实退出后才做最终wait/九端口比较/只读post，记录所有实际返回码；不是新增测试案例，不新增公共.py或覆盖原件。用途/私密sourceSHA见user-demo-operational-binding.json。最终serve-driver-receipt/post-run-proof/post-receipt尚未产生，cleanup_success/actual_exit=null，不能称4h完成或通过。

根私密.submission-private/完整演示登录说明.md已0600保存页面入口/准确版本/有效截止/双合成项目范围/普通合成账号/提前stop和状态位置；公开不放密码。界面http://127.0.0.1:5178，API18088，与原5173并存。停止请用私密owner记录的精确stop_argv，只发拥有权请求；实际结束须看statusfinished/cleanup和外部wait/post。

交接后root监测后台，不让agent同步等待四小时，也不把此进行中状态当云常驻、独立/性能/完整4h最终验证。所有进展记录均带观察时间，公开/私密输出secret扫描只覆盖当时已观察字节，未来新日志未被提前宣称扫描通过。
