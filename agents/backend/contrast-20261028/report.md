# 新源790开发夹具交付及真实验证

作者/执行者：后端AI。设计bdc9f99b先于工具；本岗没有云/浏览器/CI操作，没有产品源码变更或独立验收执行。新云目标a12e9e70与26d6328a产品字节一致；相对f4仅catalog审计修改。测试使用Git材料化的准确a12 53文件快照，不能把本岗f4 worktree冒作新目标验证。

## 产物和边界

- `790_bootstrap.py`：root宿主Python3.10，精确实际binding、新P7/P16 namespace、过期窗口、18应用表空、全部实际源文件bytes/modes、原CLI三个用户、原seed_demo V2。口令只stdin/0600，原seed44/04:00Z同锚，迁移表不算可空业务表。
- `790_host.py`＋data工具：原data-only admin执行S1。实读SQL/用户/成员/容量/依赖，选441对、882不同任务，原CLI服务scope40项目，核实际auth_sessions摘要及提醒未变。
- edge工具：source-free stdlib，实际严格CA/绑定IP端口，原HTTP登录三人，GET/contract及真实提醒create+新key dedup。源/namespace/CA/binding/期限与私包必须一致，prepared窗口600秒不延长真实TTL。
- `790_load.py`：root LOAD宿主Python3.10，同一只读stdlib edge工具；任务offset0/1/41分别80/800/8000请求，真实版本私包链、入口/出口版本摘要、无重试，错误/截止/不完整都fail-closed。根只接metadata，私包按已有受限TLS/一次性加密运到LOAD，不由聊天传私包或令牌正文。

完整命令/hash及角色限制见[runbook](runbook.md)。当前v2七文件manifest SHA640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84，split-v2三段投递含完整APP/LOAD工具，逐文件bytes/SHA；旧manifest-v1和原投递字节保留。data代码不会进入edge容器；edge容器不接产品/DB环境。旧935包、账号、控制器与历史结果未修改。

## 执行验证

13项最初修正版守卫全部通过；随后完整15项开发目标首次及扩展后均通过，不能相加成30项唯一测试。15包括真实derive_texts→generation AST的binding schema、旧源/旧kind/F/错库/错worker/错入口/过期拒绝、私有mode/symlink与O_EXCL、3.10语法/UTC-Z、source-free导入，以及一个完整真实CLI/seed/handler链。

该真实链在独占SQLite中执行原CLI创建三用户、V2完整40项目/6000任务/9000边/15000记录，实际SQL核441对882任务充分；原服务CLI真实签scope，S2验证四个真实任务对的创建/去重，再两个循环八HTTP请求；offset1只增加所选任务版本2，其他三个不变。另在同一用例注入计量deadline终态：工具返回1、续包resumable=false且拒续；真实SSLContext使用公共CA验证CERT_REQUIRED/check_hostname，错TLS scheme/旧端口/私网IP/凭据URL拒绝。没有真实TLS连接或MySQL锁验收，测试适配器不冒真实网络；其计时为测试占位，不作性能数据。

三host脚本AST按3.10解析且无datetime.UTC导入；本机实际执行解释器3.12，所以3.10运行兼容最终以root云实件为准。Docker代码运行于原已证Python3.12镜像，可正常使用UTC。最终工具Ruff/format通过。首批紧凑手写测试有18个E701/E702及import/style提示，formatter拆行/排序后消除，没有隐藏或改变业务断言。

## 首版错误与root真实回传

首版只测手工binding子集，遗漏本轮派生字段名与宿主3.10接口。root在任何云执行前截获，未建账号；a2ec7e50及旧bootstrap-delivery.json保留且禁止用。d655903a修复并采用真实派生数据形状，而非改测试接受旧schema。

据root实际回传、并非本岗云执行：bootstrap-v2 invoke t-hz071dhyyg2hb0g成功，实际manager1/developer2/reviewer3；V2 seed44/04:00，40项目、40迭代、6000任务、9000依赖、11400 reviews+3600 decisions；auth/service/outbox/escalation/notification/scan均0，audit40，完整53文件核同。S1/S2与负载的后续云结果未预填。

## scheduler与正式验收

当前协议要求S1选中任务没有提醒、S2真实创建并去重。先开scheduler扫全40项目会改变前提，必须拒绝。root明确本次先做scheduler尚未启动的6-role开发配置对照；没有关掉已有必须后台然后自称正式。正式7-role另用新namespace、真实scheduler scope与首扫终态，专门协议快照稳定已存在事件/任务版本，走dedup-only并与独立功能fresh-create分开。现790不能直接作为正式600秒准备或独立792工具。

旧f4规模5862/超762是其旧精确字节结论；新a12规模由根另计，本岗不预填。7/16真实性能收益、完整资源尾部和正式独立验收仍待root按新源执行。全部为AI过程材料，不替写学生亲手研究总结。

## 审核阻断后的v2协议修复

审核岗经root单向派发发现：S2共用Client在入口后未逐次核硬截止；S1长SQL之后仍可能调原service-token CLI；一worker失败后其他worker仍发后续操作。全部是新增开发诊断工具问题，不是产品漏洞，也没有云假绿：root当时尚未执行任何S1/edge/LOAD。

先在原c3ba1889… HTTP / 原6b4f9ba0… S1字节上留14个真实无网络断言红：8种新/复用连接到期派发、connect中到期、socket预算15s>剩余2s、2种shared abort、双worker屏障后仍发剩余3操作、S1只读跨截止仍签CLI。没有setup错误或网络。a43f60e4先保存红例，原XML两处pytest尾空格使diff-check exit2后仍提交，属本岗流程失误；现在保原Git历史和本地raw，另gzip逐字roundtrip及双SHA，不删改红例内容。

v2 Client在派发前及connect后检查min(stop_utc,HARDSTOP)和abort，连接/既有socket的下一等待上限取绝对剩余秒。请求已经派发后允许读取其真实inflight结果，仍受绝对期限；记录dispatch_attempted、headers/body完成情况，过期留下前缀，不重试、不假称零请求或全局回滚。每worker共享Event，错误/截止先置abort，其他worker不再开始后续操作/周期，barrier失败也传播；完整数/失败/截止/abort任一不满足都禁止续包。

S1在CLI签发派发前、返回后新校验事务前和最终候选前重核窗口；bootstrap、APP-host、LOAD所有工作子进程调用前/后重核，timeout不再固定600/240而<=剩余授权窗。已经被准入的CLI/POST可能留下部分真实状态，超时保留并仅按精确owner正常停止，不自动重seed或撤销旧凭据。

原14红例修后14绿；加原15真实CLI/V2种子/handler兼容及4个inflight/host等待边界后最终33项唯一目标全绿，保留原13/15/29/31等中间结果、不累计为更多唯一测试。最终Ruff/format通过，无新云/CI/独立运行；33绿不代替root审核或真实P7/P16性能。
