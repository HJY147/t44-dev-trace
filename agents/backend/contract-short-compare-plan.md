# 契约校验旧/新有界短对照：待运行

根已收方案；当前独立UI/主题开发优先，**没有安静窗口授权，不运行、不启动服务、不改生产**。930仅预留，未创建；不占后续编号，不读取测试岗脚本/数据库/结果。

## 精确对象与资源

A=4c20f32b71635016815420472b9d4bb4fa850df0；B=5dcb73cc10c38deb14fae68d33318b04d538fecf。已静态git diff确认backend/t44仅runtime.py净+7，依赖锁/包配置相同。两者HTTP版本、候选Schema、项目fixture及其它业务字节一致；生产B已412开发CI/限定审核，不能代性能收益。

仅自有t44_profile、127.0.0.1:18083、同venv/Python依赖、1worker、同线程40/pool5+10配置。不给pool或验证打补丁；无timings/cProfile hook扣减，只测相同未包裹API。4worker/400VU/600秒/P95≤270ms正式条件与失败保留，不外推本短样本为达标。transition/escalation和源码5980超限均不因本比较解决。

需要根协调独立UI/部署/DB/渲染暂停本机负载。阶段开始/结束发UTC与实际进程状态；记录操作系统/CPU/负载、MySQL版本、worker/thread/pool、依赖版本及是否存在其它共机进程。只记录计数/状态、源码hash，不记录口令/DSN/Bearer/自由文本。

## 一次控制器完整执行（拟930，尚未实现）

1. 从Git精确对象导出A/B生产快照至本项目ignored目录，无新业务分支/产品改动。子进程在任何t44 import之前固定sys.path/PYTHONPATH。记录tool_commit与app_commit分别的值、所有实际t44模块__file__/SHA及资源SHA，并与对应git对象字节核对；不能把新HEAD误写成旧应用实际源。凭据仅读ignored0600环境/账号，选库必须同时验证t44_profile。
2. 同一持续控制器完成所有start→ready→请求→stop，不依赖下一次模型调用。按A-B-B-A启动4个独立服务；每个phase绑定同18083、同参数。首A通过公开API bootstrap创建明确合成项目/成员/迭代/task，私密fixture0600；后续只读同一候选payload，fixture不重建，底层task/version不写。三个候选各验证HTTP200、valid=true、无violations、business_guards_executed=false及operation/category。
3. 各phase先1并发3类sanity；然后同8并发每worker15次预热，共120个正确请求、每类40次。预热不入主样本，预热≤5秒/不足120或任何错误立即失败停后续。
4. 每phase只跑**8并发8秒闭环**这一个组，候选按相同循环/worker偏移分布1:1:1。实际每类计数随最后在途请求略变，逐项记录，不声称样本数完全相等。客户端trust_env=False固定回环，不关闭TLS校验；工作线程/HTTP连接策略完全相同。
5. 保存每条E2E/status/valid/category/request_id和实际时段，统一nearest-rank ceil(p*n)的P50/P95、均值/最大值、吞吐/错误。四phase分别报告，不平均P95伪造新的P95；若跨phase汇总，须从原始样本重新计算并单列。Server-Timing只是worker内区间，不能称总延迟。phase进程CPU/墙钟包括相同启动/预热/空闲范围，不能冒充纯主样本CPU；可对明确PID低频采RSS/CPU并标采样分辨率，不查环境/完整argv。
6. 每phase完成主动正常stop并wait，finally清理本控制器拥有的PID；不触18080/其它服务，不留空跑timer。全控制器deadline90秒，预计45–60秒，预留≤2分钟窗口；失败/超时保存已收原件并停止，不自动重跑补绿。控制器RuntimeError不能覆盖为成功，部分有效样本与整体状态分列。

## 准入与结果界限

先由根确认最小工具/窗口，再创建930并静态核对、commit后报告精确tool/app源，才执行一次受限命令。原955及03失败/样本原件不改写，不重复03的baseline/timings各1/8/32矩阵。工具若不能保证actual-import身份或生命周期，先停在准备状态；不以目录标签当源验证。

结果仅观察这一自有fixture、1worker/8并发/8秒的短对照及ABBA波动，不是正式负载、独立验收或对生产全部接口的证明。若错误或环境漂移，直接保留结论不稳；不删除鉴权/撤销、锁/CAS/幂等/独立审计/outbox/Schema来获得数字。是否继续写路径测量/优化由根根据新证据另选，不自动扩大到400×600或新SQL路径。
