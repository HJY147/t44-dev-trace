# 一次有界campaign运行准备结果（idle，未判独立/性能）

root明确先前短窗口低估了串行准备/独立核验成本，F7与R3都未获phase或发负载；不能把调度问题记作产品性能失败，也不能缩630秒凑数。先aa73585设计，再adc5197固定F7/R3 helper SHA分层派生两新namespace，source c8/实际archive c393不变；仅新BASE/runid/明确UTC窗口，旧leases/grants/manifests不改。

旧F7按原时限auto停止，09:27只读核全部owned/children absent，无需信号；旧R3 metrics正常stop/final raw SHA/bytes复核，appguardian和broker guardian经owner核对正常SIGTERM全停，无强杀。七类旧原件hash前后不变，所有raw保留在ignored原目录。首次R3端口后验24397 EADDRINUSE的false保留，09:30准备前所有指定端口重新bind-free才复用；sharedMySQL7980和generator不发信号，不改旧数据。详细stop原件与旧interval final见本目录。

新F-campaign09:30:58实际API4worker/consumer及独立broker/guardian idle启动，严格CA/IP401；新P-campaign09:31:04实际API7worker/consumer及独立broker/guardian idle启动/401。两新run/CA/Cookie/vhost，复用原明确t44_f817与t44_p829c及各自appenv，不重建数据、不seed、不读identities/admin/独立目录。各初始native-build一次新冻结：F SHA8f7ac784852f46d68c5a33b3780f620e4c76f07118562047246c2f7a295260c7（7真实应用process），P SHAe88e88448b387c0f938aec7a5f78f1efb72461e9b615139964ee311608de2397（10process）；scheduler初始pending，后续root scope只添receipt不改初始build。

共同新spawn cap10:00覆盖动态scheduler，不绕旧09:20；F-app10:20:30/broker10:22/force10:25，P-app10:30:30/broker10:32/force10:35，P interval10:29。root另限定F phase≤09:45/P≤10:15，phase许可与资源lease分开；root先真实预检API/CLI/单scope/sealer链并声明neutral preflight project，再给独立operator，部署不代做case或造数据。F/P严禁同时负载，root真完成后可提前normal stop。

P1s sampler74003于09:31:05实际独立运行，原guard raw保留；新root明确generator PID须注册到本run、预热前至少一个delta间隔，缺失/首点null，不冒满coverage。MySQL标shared全进程，RSS聚合/CPU一核100语义保持；最终receipt尚待10:29/提前stop，未预填。四项本岗campaign纯guard0.25s、Ruff/format/diff-check通过；新schema/UTC差量逐字可逆、10:00门禁包含动态scope、旧deadline变更拒绝。root负载/独立结果/新campaign最终停机回收均未由本结果判通过。
