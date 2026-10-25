# 原生功能候选部署状态（运行中）

部署AI，2026-10-25。本阶段完成新本地隔离环境，未开云、不操作旧MySQL/旧库/旧用户/旧服务，不是正式性能或独立验收结论。先设计ad9ada1；初始ade5精确运行子集准备保留，最终应用只在root明确准入后绑定并运行c8cea7e82805de5283ce67501769fa9a4efc1047。代码与过程产物均由AI完成，未冒充学生手写研究报告。

新broker使用25696/EPMD24396/distribution35696/CLI45696–45705及全新Cookie、user、vhost、data目录。ade5原控制器SHA a251989f…逐字派生仅3组明列差量：两处端口常量和两次同一broker父目录文字；私有cookie前置setter、严格认证、权限、回环与PID拥有权/关闭逻辑未改。07:12:29UTC实际start/inspect成功，包括文件Cookie与服务端相同、新密码认证、唯一无tags用户/vhost和固定资源权限；EPMD实际127.0.0.1及::1，均回环。原HOME值保留、nocookie显式阻止默认cookie读取，没有设置共享旧环境HOME或写用户HOME。

首次prepare真失败：可迁移OpenSSL仍尝试读取构建机不存在的openssl.cnf。7e96931失败回执与原始私密stdout/stderr保留；01df352给该子进程显式本轮私有配置、fresh目录重新prepare成功。实际Python锁3b15a7bd…匹配已有依赖，真实inventory/pip check通过；未重装项目依赖、未重新验证wheel字节。新CA/localhost与127.0.0.1 SAN/用途/签名/keypair已真实核验。

最终c8实际Git archive字节保存为私有source-archive-c8….tar，SHA256 c3930f0c6fd5907ace0b860ae0964746eaf006d8722de975628f4832bd2b3bd9；只含backend/t44及两份后端锁/配置，共54件运行文件，不含独立目录，也不声称全仓checkout。原ade5源和manifest未重写。新application绑定记录每件hash、树OID、真实import路径与锁；artifact-manifest SHA 2dcbffa45fe2dedb50349c4e12d1587300db069811fad4816ea4a8ac6648ca41。

root准入后07:24:49UTC实际API supervisor23583、四worker23585–23588、consumer23617启动，均独立session/cwd/精确源，worker另核PPID/UID/PGID/命令指纹。严格新CA+IP无凭据projects请求401；07:26:48另用curl保存原始headers/body及hash，未用-k。401只证明TLS/鉴权路径连通，不代表业务或故障通过。scheduler当时未启动，未伪造PID或ID。

native-build.json只生成一次，SHA c6eafe3c1ac398e226fb977ab48919421f9f25aa3470c57ffcaaa94842ce45ec。kind=native/image_digest=null，源c8、archive/artifact/锁、实际执行文件、Python版本/arm64/inventory、canonical无秘密argv、7个真实应用process（supervisor/4worker/tracker/consumer）齐备；scheduler_pending_scope=true。Rabbit4.3.6由本轮认证RPC实测，MySQL8.4.11明确root提供；未用treeOID充archive哈希。后续scope provision只追加receipt，不覆写用于grant的初始manifest。

本岗10个broker/文件/时窗/拥有权合成guard通过0.05秒；最终14个应用DB边界/expiry/子PID复用/执行前hash/采样失败仍清理guard通过0.04秒，前12项不重复累计。Ruff/format/diff-check通过。初稿3个unused import与新增guard的import-order修正真实记录；不是产品测试失败，也不编造未保存的初稿原字节。

scope门面为scheduler-control.py：root明确提供单project/私有token/UTC expiry，先用新app CRUD连接只读核该唯一session对应token、service actor、actual单project_ids、escalation:write、未撤销/active、TTL3600和expiry，再owned stop/start。stop在尚无scheduler时已实际执行absent/success；截至本记录没有给定token或实际scope replacement，不能称其数据库probe/调度周期已通过。旧token不撤销，替换后只新project周期扫描，旧项目覆盖不作虚假承诺。

fault-control.py仅给root可选mq-stop/mq-start/consumer-stop/consumer-start，未执行故障动作。mq-stop语义是官方graceful shutdown而非SIGKILL；恢复仅本轮PID都消失且新端口free后归档自有旧active-record，再保留原node/cookie/vhost/data启动。原控制器不支持已有record直接重启，这一限制明确处理；不清库、不重贴旧失败，不把新工具代码当真实故障通过。

守护仍独立运行：应用watchdog23577在08:46:30UTC停止本轮应用并核已登记worker；原guardian19996在08:47UTC停broker/EPMD，08:50为总硬停止计划上限。两条私有NDJSON流分别采拥有权核实后的服务/worker ps CPU/RSS/elapsed与UTC/monotonic非原子anchor，尚未结束/导出，不当性能验收。实际停止、全部PID/端口absence及完整资源文件回收仍需后验记录。未读取任何独立目录、identities或admin，不联系独立tester；只有root可据白名单交中性环境与生命周期能力。
