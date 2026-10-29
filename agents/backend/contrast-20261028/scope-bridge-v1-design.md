# 可预装scope桥 v1：LOAD准备、APP有限执行、LOAD原子交付

后端AI，ROLE-backend-SCOPE-BRIDGE-V1，2026-10-28。只本地代码/测试；无云/SUT/SSH/新权限。新tmp/790.../scope-callback-bridge-v1，旧失败、已结束nonce、原草案、v2/v3/c222不改。仅SERVICE_SCOPE_REQUEST，不实现撤销/ROOT_ACK；撤销由原工具auth/logout。已核的旧PUBLIC grant/launch/supervisor只参考形状，不复用其值或授权。

## 根交给桥的显式中性输入

- 每个原件单独传入path+精确SHA：实际request、已验rootgrant、launch、supervisor receipt、F binding、neutral runtime identity；允许PUBLIC投影携带这些原件的解析值及各SHA，但必须逐文件SHA反查，不能用root_verified布尔代替绑定。
- LOAD observer locator：本次独立container完整ID、实际host init PID/startticks、supervisor实际host PID/startticks及PGID；只有PID元数据/进程state/容器state，不读其private/env/cwd/测试代码。PID9是容器内PID不能冒充host PID。根需在实际启动阶段记录host映射。
- 手握手目录与本nonce request原件的固定相对关系；输出只有相同nonce的sealed.PUBLIC.json。authority额外随机bridge_id不替换request/context nonce，不改context字段或加入execution-build；execution build从grant+launch另核。
- 公钥域排除列表由root填入本次初始输入key和operator证据key SHA；scope key必须RSA3072且不同，私钥不属于桥。binding source/full archive/image、neutral runtime/CA/endpoint/DB/project与grant全链相同，phase必须functional/F，no_retry true。

## 三步、时钟与观测性边界

1. **LOAD prepare**：核实际原件、全context、grant/launch/supervisor nonce/source/freeze/expiry、request IDs，核本机owned container和host PID/startticks/PGID在运行、当前nonce request仍pending且无reply。独占reserve nonce状态；记录UTC与本机monotonic观测。callback原120秒不改，deadline取request.requested_utc+120、grant/launch/supervisor/binding stop最早值；LOAD本机映射monotonic并受supervisor hard monotonic限制。导出短期authority，最多80秒且为最终LOAD交付留10秒。此处alive仅是LOAD本次观测，不是APP远程持续存活证明。
2. **APP provision**：authority/rootgrant/request/binding/neutral全hash及context再核；拒陈旧/过期、已消费、错误key域和已结束grant。APP只在根给的新鲜LOAD authority下有限执行，记录自身UTC/monotonic，不能把LOAD monotonic当本机clock。启动GEN前binding stop至少600秒，且剩余callback预算满足预设限额；所有动作共用有限deadline。先原data-only SQL只读核实际project/iteration归属和source，再原GEN scheduler-token（首次）或scheduler-rotate（已有owned scheduler），然后scheduler-start。核真实owned scheduler image/labels/Running/restarts0、同private credential文件只读挂载/环境指针；在data-only原authstore用token digest核actor2/active/exact project set/scope/expiry，保request原有ID顺序。最后原SEALED_SERVICE_SCOPE wire密封给该request公钥。token/K仅私密进程内，不进argv/env/stdout。root只搬opaque及有限PUBLIC receipt。
3. **LOAD deliver**：回到实际LOAD重读原件SHA、同nonce pending、owned container/supervisor仍live、UTC+本机monotonic deadline；不信APP的alive字符串。只做opaque envelope/header匹配，不持接收私钥、不解密token。先同handoff目录O_EXCL/no-follow临时文件、固定FD写/fsync/chown为原operator UID，再紧邻一次live/deadline检查，用hard-link原子发布到从未存在的nonce.sealed.PUBLIC.json（不覆盖、不让consumer看到半JSON）。记录检查时刻及发布时刻。进程存活检查与文件发布不是跨系统原子事务，公开这一观测限制；原工具仍独立验MAC/解密/业务。

APP无法证明LOAD在其执行期间一直存活；若LOAD期间结束，最终deliver拒绝。已有服务端in-flight可能完成，保留partial/uncertain事件，不假称回滚或零请求。所有失败停止本nonce、不自动retry/resume；after-mutation失败标phase隔离，待root新窗口/明确处理。只终止桥自己创建且pid/startticks/PGID核对的宿主子进程组，不擅停其他服务；Docker/数据库已受理动作可能有迟到副作用，必须记录而不能靠成功exit掩盖。

## 本地验证门禁

无SUT模拟：wrong source/namespace/grant/nonce/key/context/过期/陈旧快照/owner PID复用/旧container/已结束LOAD/pending变化/重复nonce/覆盖均必须在provision前失败；fake controller记录零mutation。跨机clock测试不相减两机monotonic；原120秒与late-return拒绝保持。真实原CLI service-token+原Rows/Settings/SQLAlchemy SQLite验证授权project/iteration及auth session，credential只内存；实际RSA-OAEP/AES-CBC/HMAC roundtrip按原PUBLIC wire解包。首发、后续rotate、timeout/inflight/无retry、原子deliver和原ACK缺席都检查。SQLite/模拟Docker不是MySQL/真实两机/性能/SUT验收。

## 交付与下一次运行前准备

root VM仍停时完成全代码/manifest/小分片安装/执行模板/公共依赖清单与限定review，再集中开原VM。依赖为宿主Python3.10 stdlib+Docker CLI+原GEN绑定、backend原image中的Python3.12/锁定cryptography/SQLAlchemy/PyMySQL/原t44 CLI。真实新源/新F/新authority仅由根下一窗口给，不能把本地mock或旧grant填作actual。
