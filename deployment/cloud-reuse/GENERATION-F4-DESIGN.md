# 新 f4 generation 与连续资源镜像：实现前检查点

来源是root本次明确调度，不改变旧935环境/770d/56d78/546e/停止租约。产品固定f4bd382d4668130793fc553df9ce6363c4656ea6；新工具不控制浏览器、费用、VM、SG、IAM，不读独立用例/799或800 PRIVATE。仅同批app/load私网两节点，root执行实际云动作。

## 新generation接口

`generation-f4.py prepare` 必须给root pin的derived upgrade-binding SHA、其完整本地derived OCI archive、来源五文件包与manifest SHA、原30b1七角色proof、47b50 proof模块和daaf旧生成器只读副本。新程序重新核5200 builder身份、f4/revision/archive/config/descriptor/layers、来源53文件，真实`--rm/networknone/readonly/10001`容器核完整t44＋两个依赖描述的文件名/bytes/SHA/mode（53项）。旧web935本地actual身份与同字节前端清单绑定，仅原标签，不冒f4编译。所有官方基础角色重新匹配原已证明不可变身份。

F/P新runid/project/database/user/vhost/volume/CA/端口；prepare显式F/P TLS与loopbackHTTP端口，不碰已占端口/旧project，不接旧13306。原`python -m uvicorn t44.api:app`，无810/额外PYTHONPATH；F4/P7为本轮默认，P其它获准值必须每次显式记录。nginx五类temp全部/tmp，原证书/101/readonly/capdrop保留。

每phase复制自己的controller和固定daaf只读library；binding pin两份代码和compose/env/nginx，`arm`创建本phase持久timer与冻结binding/controller的ExecStart。所有stopUTC≤2026-10-25T21:00:00Z，start/scope rotation检查timer active和未来窗口；CLIstop只匹配本project/service＋已证明image/configID，保卷/库/原退出状态，未知不杀。旧VM06BJT计划不动。

操作拆分prepare→arm→config→infra→migrate（显式新schema）→root原CLI账户/seed→idle→root实际scope service凭据→scheduler-start。无预造ID/session/成绩。idle先API/consumer/web、同权限实际nginx-t、TLS，然后host原CA＋IP GET/api/v1/projects=401，不用APIrunning/Composewait替代HTTPS。命令失败stdout/stderr新私有原件保留，尤其scheduler失败/重启不能被success标签吞掉。

## 资源collector与私网单路径mirror接口

`resource-stream.py prepare-app` 输入新phase binding SHA、appIP/loadIP、18446可配置私网口、sampleUntil/serveUntil（≤21Z）、interval(0.2–1s)、bytecap（≤512MiB）。start部署独立systemd-owned service，复制controller/frozenbinding，Restart=no；单次CLI或前台UI结束不影响它。unit/代码SHA与PID/startticks实核后才seal/stop，停止留final记录。collector只调用Docker ps/inspect元数据和读取精确owned CIDs的cgroup/proc，不exec或改SUT。

每个expected role=mysql/rabbitmq/api/consumer/scheduler/web/tls-gateway都逐采样记录UTC/monotonic、scheduledMono/延迟/耗时、resource_id=project/role/CID、actualimage、PID/startticks、RestartCount/running、累计cpu_us、interval_cpu_percent（单核100%，可>100）、proc RSS求和bytes、cgroupmemory.current bytes、实际PID列表。API一组包含全部workers/tracker/init；RSS求和可能重复共享页，不冒充独占物理内存。第一样CPU或缺少字段/缺进程为真实null＋reason，PID/CID变化明记，不能补0或插值；多CID/身份不符拒该role而非任选。Memory.stat匿名量另列，不能冒充RSS。cgroupv2不支持则明确环境失败/缺值，不偷偷改成Docker估算。

语义来源：[kernel cgroupv2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)（usage_usec覆盖后代、memory.current含cache等）；[proc stat](https://www.man7.org/linux/man-pages/man5/proc_pid_stat.5.html)（starttime/RSS）。只派生数值，不读取环境、命令参数、DB/API凭据。原raw JSONL固定FD O_EXCL|NOFOLLOW/0600，写入及读取锁保证字节前缀一致，bytecap触及时封尾并标非正常完成；原文件不截断/覆盖。

TLS exporter只bind app私网IP单端口，load IP allowlist；只GET字面`/raw`，无query/POST/目录浏览/任意路径。专用随机nonce仅`X-T44-Telemetry-Nonce`头，在私有handoff0600中给load，禁止日志/URL打印，不是业务token。服务器只读原leaf server.pem＋server.key建立TLS（必需leaf私钥，不读CA.key）；load只得公共CA。单路径内容仅数值资源raw，不传账户/DB/API token/源码，不接SUT REST。

负载端`prepare-mirror`只接受root转交的独立私有handoff，固定appIP/CA与本机load sourceIP，header offset＋chunkSHA/streamID/binding pin；只将app原始字节append新0600mirror raw，offset不跳、不得覆盖/截断、起点必须0。后台独立systemd服务持续pull；采样结束后app写final尾标记（此前prefixSHA）并fsync，独立wholeSHA/bytes通过headers封印，再服务到serveUntil。mirror必须收到全部finaltail并核wholeSHA才声明transport_complete；断线/超时/after-only/不完整收尾明确false，不推导验收。

interval开始必须早于warmup，sampleUntil覆盖完整steady和收尾；记录actual第一/最后样、最大真实gap、延迟、null/重启和tailhash。可给显式requiredStart/End得到仅时间包络检查，不代判独立工具完整性/性能。单机本地合成unit tests与云真实proof分别记录；实际端口可达/资源粒度、whole mirror完整回收待root执行，尚未预填。
