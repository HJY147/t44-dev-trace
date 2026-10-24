# 930 ABBA工具准备：尚未运行

实际夜间续派遵循05623c的短对照计划。独立worktree分支codex/backend-contract-abba由本岗05623c创建，再合入根75c3468；合并基点2a34243476461f4aab0c29ec383aa37766b93c9c。生产backend/t44逐字同5dcb，未改生产/测试预期/14冻结文件。新930为开发诊断工具，不改变源码计数分母。

仅允许显式--execute的默认run模式由总协调窗口启动。该单命令拥有新建进程组，内部controller依次管理A-B-B-A四个独立服务和各自finally收尾；controller预算78秒，监督进程86秒发TERM、89秒KILL，最终目标90秒内退出。只针对本控制器新建PGID/PID；端口被占直接失败，不停其他服务。controller/serve/bootstrap是内部子进程模式，不单独作为执行命令。真实生命周期/90秒收尾尚未实测，静态核对不是运行通过。

A=4c20f32b71635016815420472b9d4bb4fa850df0；B=5dcb73cc10c38deb14fae68d33318b04d538fecf。从Git归档生产包、pyproject、hash锁，逐blob核对，实际服务再次记录全部t44模块文件/namespace路径和SHA；首尾所有导出资源SHA再验。tool_commit与app_commit分别记录，PYTHONPATH及sys.path在应用import前指向该快照；无请求/SQL/runtime包装。启动事件仅观察实际40线程，不改40；pool必须5+10、1worker、18083、t44_profile，否则失败。

首A仅通过公开API创建一套合成fixture，复用已提交955的bootstrap例程，输出600；四阶段读取同fixture/同token，不重建。每阶段三个类别sanity必须200/valid=true/guards=false/正确operation且无violations，再8线程×15=120均衡预热（每类40），再8并发8秒闭环样本。线程建好Client后统一barrier启动计时，所有完成请求逐条JSONL，不保存自由body或Bearer；any错误停止并保留失败/部分样本。每阶段分别nearest-rank P95，不平均P95。E2E包括HTTP+JSON有效性检查，raw写入在计时点后；客户端group CPU含建Client/写raw/关闭，服务CPU含import/startup/sanity/warm/sample/shutdown，均不是纯sample CPU。只对拥有PID记录RSS/粗粒度累计CPU和host loadavg。

读取仅两份指定600中性资料，命令不含DSN/口令；output在本项目ignored .runtime且新建700。原955/03整体exit1和已有有效子阶段证据不改写。本工具失败也保留原件，不自动重跑补绿。

静态/helper11项通过，无t44实际import；Ruff首次隐式配置失败原文保留，显式项目backend配置lint/format通过，详见abba-tool-static.log/json。这些不是HTTP/实库/性能或进程清理证明。正式400VU×600秒×4worker、原P95失败和源码6051超限仍未解决；本对照只观察一个自有fixture的短样本，不据此推断transition/escalation。

等待总协调明确120秒quiet窗口，不能按时钟自行启动：

```sh
.venv/bin/python tmp/backend/930_contract_abba.py --execute --output '/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/backend-contract-abba-night-01'
```

应用启动/样本/退出是否成功均待执行；当前无本岗诊断进程。
