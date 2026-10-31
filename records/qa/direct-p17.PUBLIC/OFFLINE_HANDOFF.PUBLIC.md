# Direct P17 离线交付与准确限制

冻结QA五源未改，身份见tool-manifest/RELEASE；DIR=records/qa/direct-p17.PUBLIC可独立搬运。RUN=bootstrap_run_id=producer_expected_run_id=r30posttools17，W=/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17，REMOTE=/root/t44-direct-p17；material_run_id=r30materialposttools17只用于外部运输绑定。新nonce/default-false binding不表示当前已有真实会话/packet或现场批准。测试只生成本地合成材料，未消费真实远端case。胶囊可本地解包、10成员全SHA核合，独立于旧PRIVATE；Mac没有原LOAD RSA私钥和Docker，不能伪称原INSTALL真实Linux成功。

## 已完成的真实传输验证

400个真实Python HTTPSConnection连接本地TLS服务（CA/SNI验证，最低TLS1.2），完整大历史8582次HTTP请求。原40秒后置预算内29.452932秒，400最终快照/400完整审计，全线程/验证池/writer退出，reserved最终0，deadline=false，无post错误。不是内存HTTP fixture，也不是新11分钟测量。8582条raw认证完整，plain609229172B；本地密文备份74819093B、7文件认证解密与逐文件SHA通过，SHA7955da4f610bf842363a671076f64e853b399bba7539a830f54b7da780c38f09。本次小备份验证不等于本机实际运行28GiB sealer。

pinned producer bootstrap cc94bea2ba0699cf0c81b3cf5ac6c5ffe3277ee2a6b78e100885cee7c5475d27 / support bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170 的实际collect/assemble/host_main与support TLS request/分页执行，经83次本地TLS请求写出DIRECT，再送冻结BOOT.initialize并构造原runtime/TLS连接。中文旧packet canonical绑定通过、400/800映射和新CAS版本通过，RUN三处相同；SQL/serviceCLI/Docker/root UID为明确合成适配器，不冒生产登录/真实DB容器证明。详见PRODUCER_BOOT_CHAIN。

## Linux真实资源限制尚未验证

本机没有Docker、Lima、Colima、Podman、UTM、Apple container或brew。仅官方Lima API元数据可读；binary下载60秒0字节超时，校验清单连接10秒超时；未安装二进制、未启动VM、未做系统权限安装。按本轮边界已停止环境扩展。机器8CPU/24GiB不能据此声称Linux8CPU/8GiB cgroup、amd64精确LOAD镜像或28GiB封存资源已经通过。本地TLS结果不保证现场40秒；下一次开机是实际验证现场，不是重述已通过现场。

## 具体原因与修复证据分界

原云端Direct16的HTTP200/完整body后schema验证等待于post+40.004s超时，其后约11.1～15.9ms出现13断开与1None.close，符合原全局stop集中关闭连接行为；逐个生产stack因果未被证明。旧后置5106次、auditURL4863互异，没有共享项目页可省，原Validator已每进程缓存，主要改动为编译重复字段/ref校验、8个post验证进程/64个I/O槽和有界owner收尾。当前冻结源对同5092真实完整页的孤立校验：原28.804846秒，新18.714388秒；它是本机schema对照，不是整体云加速倍数。v1 memo寿命与v1.1 reserve门禁缺陷留存，v1.2六阶段边界/10000寿命/2400变异/退出码回归见本目录；不吞错、不晚计PASS、原40秒和400要求不降。

原Direct16依然性能指标PASS、后置不全总体NP，157未观察不补写。当前无云/SUT/原服务器SSH，没有通知用户开机，也不自动开机/重试。
