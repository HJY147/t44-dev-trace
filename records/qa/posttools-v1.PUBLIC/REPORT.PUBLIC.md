**已确认编译memo对象寿命缺陷：此冻结版本不可部署/不可批准。源保持原样，修复另建v1.1。**

# Posttools v1 候选：仅离线，待新独立工具复核

原Direct16的NP、243快照/227审计/157未观察及16后置错误保持原事实，本候选不补写旧验收。

准确基底runtime.py为9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a；有效执行由该基底、新post_runtime.py、新compiled_post.py、新BOOT共同组成，所有SHA及组合binding见tool-manifest/RELEASE。不称整个有效runtime未变。原Run.client、call、conn、task_equal、val_headers和Metrics为相同函数/类对象；_execute在测量结束之前的字节片段完全相同，SHA d522db77778d5bc81dff7c78f9910ac45a137d7e4c6da7b5d43b73e39bf19706。

## 真实原因与改动

已认证raw后置5106次，audit GET4863次、URL4863个互异，task_id+page过滤，无重复项目页可共享。原验证器已经每进程缓存OpenAPI/Validator，不是假称每页重建。候选将原全部schema操作编译为缓存闭包，减少逐字段ref解析；仅post阶段8进程验证、64个I/O槽。保留完整task历史分页、每条task/project作用域、原outcome/actor/operation/kind筛选和全部本次audit IDs集合包含断言；不引入sort/date/ID过滤，不提前结束历史分页。

40秒仍是后置成功预算。届满拒绝新dispatch，在途HTTP/验证先有界退出（请求原15s，清理grace30s），再在owner线程全部退出后close连接、join验证池和writer。晚完成明确DEADLINE_UNFINISHED/NP，不能计预算内成功。HTTP/schema错误记录并使该client ERROR，不广播全局stop立刻关闭其他在途连接；错误不吞掉，不改400/400要求。每client enqueue/admit、HTTP dispatch/exit、验证等待、deadline、owner/drain/close/pool停止事件写入私密时间线供封存。

新BOOT退出码只在metrics+全部400后置+日志完整+pool/writer停止等combined满足时为0；metrics FAIL为1，NP/缺项/任何post error为2。非零仍走原正常加密封存/回收。原Direct16 exit0/NP历史不回写。

## 实际本地回归

5092个完整真实响应与2400个变异响应：原验证器和新编译器接受/拒绝结果完全一致（2000个变异双拒绝、400个变异双接受），原post assertion AST全部保留。13项实际BOOT worker退出码测试通过，包括原metrics PASS但independent NP、503一错/399成功、late/pending及writer不完整均非零。

|内存传输重放场景|实际结果|清理与完整性|
|---|---|---|
|400合成互异task完整大历史，8582次dispatch，40s原预算|400快照/400完整审计，26.918s|全部owner/pool/writer退出，raw完整，读时并发close=0|
|400 clients，1s预算、响应延迟2s|64真实进入read的阻塞fixture，400未完成；无晚完成PASS|末HTTP退出2.014s，owner末退出2.173s，global close2.184s；post_errors0，raw完整|
|1个HTTP503，其余正常|399完成、1 ERROR，非PASS|8565条raw完整；owner/pool/writer全退出，close race0|

正常场景末HTTP退出25.557s、owner末结束25.559s、global close25.570s；没有任何deadline后新dispatch。详见NORMAL/DEADLINE/FAULT/SEMANTICS/EXIT_POLICY。变异差分的第一测试检查器曾因源码缩进解析错误失败，已保私密stderr并只修检查器，最终差分完整通过。

这些是**内存阻塞传输重放**：使用已认证真实响应shape和历史数据、重映射400合成task/audit IDs，不是新HTTP/TLS端到端或生产性能测量。5092实际已观察页不填补原未观察157客户端。主机macOS arm64、8物理/逻辑CPU、24GiB RAM，未加Linux8CPU/8GiB cgroup。26.918秒不保证云端8CPU/8GiB必过40秒；长期资源/实际Linux验证未做。

## 包与接口

本PUBLIC可搬运，胶囊内为原基底+新post模块/BOOT及全新backup.key；root不读私密源码/key/cases。候选建议全新W=/root/t44-final-20261031/QA753_POSTTOOLS_V1、新run=r30posttools17（只作离线候选身份，当前没有启动授权/计划）。安装器与单入口仍接受显式绝对W；`sh W/public/INSTALL_DIRECT.sh W LOAD_RSA_PRIVATE`，以后真正获准时 `sh W/public/DIRECT_PRESSURE.sh W NEW_OPENED/inputs/session.private.json`。初始化保DIRECT_INPUTS_V1协议，原准备豁免不扩大到测量/后置。测量仍8CPU/8GiB/2048pids、400/60+600、四P95≤270、每分钟≥1000、零稳态错误、原10/11/12GiB日志上限。封存仍仅测量退出后tmpfs14GiB/28GiB处理，非零也先回收备份，资源不足保原证据不删数据。

目前不部署、不SSH、不启动VM、不请求SUT。候选待新无上下文独立测试岗根据中性规范复核；本自检不是该复核的替代。
