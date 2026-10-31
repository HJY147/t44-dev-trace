# p15 开机执行衔接

操作者为AI总协调；产品准确源 bcec3326b40814fdb1922bbfea7c29473b47ba47，CI 41169683822(off)/41169697472(on)全部通过。此包为离线准备，不是现场身份/资源批准或性能通过。当前VM仍由用户保持关闭；用户收到准备完成通知后手动启动原64vCPU128GiB APP和原16vCPU32GiB LOAD，并提供实际公网IP。无自动VM关机、倒计时或云stop。

## 长期连接

用户已明确授权长期密钥。若旧访问尚不能登录，在两原实例云助手各执行一次ssh/01_INSTALL_PERSISTENT_SSH.sh；同一脚本以原私网IP和原hostkey区分机器，追加原公钥的restrict无expiry条目，保留原其它公钥，启用既有SSH服务。私钥不进包。无需旧两小时授权/剩余窗口检查。用ssh/update_ssh_addresses.py将当前IP与本机原known_hosts/identity生成全新配置，再以StrictHostKeyChecking=yes真实连接。不要把旧公网IP当作当前事实，也不忽略hostkey。

## 同时开始两台的准备

LOAD：只传qa-install、qa-controls和中性coordinator工具，在从未存在的新W=/root/t44-final-20261031/QA753_NEXT_V53安装。核完整原LOAD镜像、公钥对应私钥、实际CPU/RAM、raw+备份+复制峰值磁盘余量及无旧发压。按qa-install/INSTALL_AND_RUN.PUBLIC.md执行原INSTALL，先逐项核delivery manifest；只由胶囊在LOAD解包私有工具，不给root私钥或测试明文。默认false不发压。

APP：新images包本机路径为主项目.submission-private/build-candidates/global-latency-bcec-20261031。源清单52d74144437ad77140ccb8cab44bf82c4826e4ba00b9d2dc04895f35100bcfd7，bundle清单3e09cc1bfe5074832fbb61bc2e500f5b27bc23a987c3d68f9744dd650c126d29，backend config479c406502b2e4834a0e8ab9ed3fd35e60df60601a041348b1e4a97825056f0e，web866ce20bb8cbeb55b949870b96260fb3f7437b4f8c9b54686a16138c075bdf79。按deployment的ops原入口verify/import/prove-loaded，真实import receipt与observation现场产生、root0600，不伪造路径/时间。先核实际导入/原卷/容器/镜像和磁盘空间，不在云端构建/拉取依赖。

## APP串联顺序

1. 完整保存原七角色/原Compose文件与渲染配置/Env/Cmd/资源/原卷/TLS/worker及pool，生成新images和原配置rollback计划。唯一预期环境新增为API T44_REQUEST_DIAGNOSTICS=1；workers配置64及其余原资源不变，现场实核。
2. 镜像加载后，按实际ID停止原owned api/consumer/scheduler/web四容器，保mysql/rabbitmq/tls-gateway和原卷。核旧controller和其它writer已停止，实际排他后才plan/apply保durability的PL1三变量profile。新plan绑定当前事实和原值，检查空间、逐步receipt和实际resize完成；保flush_at_commit=1、sync_binlog=1、doublewrite。SET失败保留partial，不自动重试/回滚。不做盘压测/AB。
3. 以准确配置及新overlay执行计划的up --no-start --no-deps --no-build --pull never，只重建四应用角色，不启动worker。snapshot_phase如实记录两个worker为停止状态，不冒称最终healthy。仅启动新API/web，核诊断确已开启和真实source/runtime/64worker配置。
4. 使用backend新release和deployment/sequence做原资格维护及fresh material09，不seed/重建库/新建任务，不覆盖旧800任务来源；新run=r30manualp15/material=r30materialresume09/maintenance=r30restoretransition09。所有模板仍false，root仅在实核现场owner/原件/排他后填写自身批准。当前七角色snapshot和root生产批准不能替代独立QA审核。
5. 原子轮换scheduler token后，再启动实际新consumer/scheduler ID，取得rotation后真正新started且完整finished的扫描。失败保持现场，900秒仅scanner observer边界，不停止VM。最终七角色必须真实healthy并重核配置/卷/排他，原session最短余量须覆盖真正触发后的900秒。
6. 原cms_five_transport.py原字节运输新五件（原片保存byte/SHA）；全新source/bundle/import链与旧cohort历史链分别保留。LOAD独立测试岗根据真实中性事实核profile/工具/会话/资源/排他/fixture/未消费路径，再运行新的ISSUE_ONCE_P15；协调者不自行填写independent-review=true。
7. 新独立once grant实际成立后，coordinator/dispatch_once.py只调用原ENTRY execute一次。400客户端、60秒预热、600秒稳态、四类P95≤270ms、逐分钟≥1000、零错误和原业务/后置断言全部保留。raw所有elapsed/status/完整headers保留；diag缺失是unknown，不丢慢请求、不补0。代理抽样诊断本轮不开启。沿用已审原字节coordinator/manual13-observe.py（SHA67cb55f1…，文件名为历史名字但不硬钉旧source/ID）；只绑定本轮真实七role ID，在同一正式稳态的前段与后段各取12个5秒间隔样本，保存MySQL摘要计数/redo/checkpoint/已有wait覆盖、cgroup与实际worker进程CPU ticks，输出全新路径。单次120秒仅观察进程期限、无变更SQL/压测启动/VM控制，不是额外对照实验。

## 结束及用户停机

全部producer/writer退出后按qa-controls正常seal。失败用明确FORENSIC_ONLY回收，不把不完整结果改成成功；APP中性证据回收后立即通知用户可停APP，LOAD密文/receipt完整下载且bytes/SHA核实后立即通知可停LOAD，本地离线判定不占服务器开机等待。旧run/material/grant/私有结果不重用、不覆盖。永久SSH条目不随本次测试自动删除。

历史v1.2 freeze原件不改；当前14项业务规格与frontend兼容输入匹配，AGENTS过程说明有显式差异，见同目录SPEC_PROCESS_OVERLAY.PUBLIC.json与QA公开报告，不能声称当前15+1全部匹配。应用核心规模仍超限，当前性能待测，不以离线包/镜像构建通过代替作业最终验收。
