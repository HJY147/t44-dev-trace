# f7/64worker短P诊断预装交付

后端AI，ROLE-backend-P64-F7-1600，2026-10-28。只本地工具，原a12/P7/P16/10:30源与结果、scope桥e551保持；没有云/SUT/独立783或792私件/新CI/产品改动。新目标f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f，16:00Z截止；不把旧元数据换标签，不把短诊断算600秒正式性能。

8e235a34先设计；根确认两阶段准入：prep grant基于实际infra状态，只准空库和原CLI/显式seed；bootstrap必须先于GEN idle/TLS401。之后根核实际六角色/source/CA，另给short-P pressure grant；新split控制带新grant，原bootstrap记录保持。缺压力grant禁止HTTP。runtime c0268820，manifest `1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8`。

核心变更限f7/16Z/允许64及新v4准入接口。790_bootstrap/HTTP固定旧a12、10:30、旧generation_kind和仅7|16不能原样运行，已另副本。实际公开GEN6b2da1从部署e1bfc9e7 Git原件核30497B后，仅作本地binding-shape fixture；不继续用旧schema。实际f7 Git backend53文件自有只读快照提供原CLI/Settings/seed/handler。五个select子集文件实际SHA与旧值完全相同，完整53仍由实际bootstrap源探针核验。

三文件data/790_select.py、data/790_stage1.py、edge/790_stage2.py逐字同旧包；HTTP除configure新增pressure-grant核验外，18个函数/类（包括Client、worker、check_packet、main）逐字同。bootstrap的原QUERY、源PROBE、显式seed_code常量逐字同；80/800/8000、400active无think、600TTL、330/90秒门禁、共享abort/逐请求截止/完整计数均不改。原33诊断和13transport共66条assert在仅身份/时间字面替换后AST原序同，删除0；fixture改为实际新GEN形状。原transfer仅SOURCE/STOP两常量，密封算法/协议不变。

根只授权读两具名PUBLIC wrapper，先核producer0aca6af6...54fe和consumer2531d5ca...0bfe再参数化路径/实际pins。新producer/consumer预装全部临界逻辑；预算、grant、CA、key、control和resource mirror都显式配置，无旧host/image/binding默认。S2一次marker及matrix一次marker阻止同输入换目录重跑；新opaque receiver只接收/核片SHA、O_EXCL保存密文，不解密/发负载。数据仍仅私密0600文件，root只搬PUBLIC/OPAQUE。

SQL预算用薄适配器复用已审scope桥e551的原phase_operation_lock/admit_budget/live_mysql，完整代码/manifest逐SHA核后载入，不执行scope供应、不改桥。每bootstrap admin调用和整个S1数据容器，分别锁→原305f admit同actualreceipt及当前MySQL身份/容量→原命令/输出→释放。GEN由根在外执行，父不嵌套；不从384 prior推实测。根实际新phase/receipt/source/image/roles/CA/key/grants尚未交本包，模板默认admitted=false/null。

最终68唯一目标通过：原33+13、新grant/无grant零网络/角色/budget顺序13、实际本机完整安装/拒覆盖/opaque接收9；0failure/error/skip。原CLI+V2 seed+S1/S2/原FastAPI handler兼容使用实际f7源码、SQLite/TestClient，无真实MySQL/HTTP socket。FastAPI旧依赖出现一条上游弃用warning，未擅升级。新wrapper初次Ruff的未用/合并import等10项被修正后限定Ruff通过；没有功能测试红被改成假绿。宿主3.10仅AST，实际Mac/Python3.12。

13 runtime及manifest的四完整安装命令为15107/16004/15608/9499B，各加300说明<18000；新两机目录 `/root/t44-r9/p790-f7-1600-01`。实际本地安装在umask077下核13件字节/0444/目录0755，重复每片和混bundle都拒绝。生成器先曾生成7片草稿，优化为先压缩原文本再base64，最终4片无源改变；旧未投递草稿片移出本次delivery清单，所有旧版本源/结果仍在原目录和Git中。

交付工具目录tmp/790_backend_contrast_20261028/p64-f7-window1600；business-byte-proof、verification、59/9两份JUnit、delivery/四install片、APP/LOAD配置空模板、prep/pressure grant空模板齐。全部精确命令和“先完成所有预装/key/resource/config再S1/S2”的时序在p64-f7-runbook.md。root需限定review后给真实prep/pressure grant；需要新600秒正式授权时另立协议。本岗未产生新cloud性能、代码规模或独立验收结论，以上是AI过程素材，不是学生本人研究报告。
