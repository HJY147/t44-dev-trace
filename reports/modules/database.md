# 数据库模块：796服务器规范DDL探针否决/未准入

基f4bd382d；ROLE-database-CANONICAL-DDL-PROBE-v1，AI执行，非用户亲改。设计9ff75091→原型fdb1b71b→仅FK夹具修正438fea60，产品/DDL/旧freeze/计数0修改。

- root批准的既有8.4.11 binary、两新socket-only/128M实例，两新schema；实际7.559s/3.557s含清理正常关闭，tmp796/data与data2保留。无原13306/旧PID7980/oldschemas/config/env/凭据操作，无独立799/800/805/809/814 PRIVATE/runtime内容读取。
- 冻结18表226列59CHECK/35FK；ref只从新空schema执行原DDL生成，非目标marker。native合并30唯一case=8正/13原负/9新意义漂移，原公开95615项通过。首轮7FK1826是夹具设置错原件保留，第二轮只拆句修正7项，无第三轮。
- rawSHOW仅忽略表auto计数仍误拒5个真实兼容正例，含单改计数导致CHECK从_utf8mb4重表达_ascii；ASC/BTREE和NOACTION/RESTRICT也非唯一表示，A明确否决，不能改判等价DDL。
- 当前checker另真实放行DESC/列auto移除/engine/表列collation/NOTENFORCED六项，已公开报root，不在探针改产品。SQLAlchemy离线回放证明parser留DESC但get_indexes没输出sorting；Inspector快照不能直接当完整契约。
- B1已知normalizers+migrate等保留219行，新增代码前最多省84；加68–115估算源码投影287–334，生成器另计。B2未实现/未证明；不宣传100–250净省。原应用5862超762保持，本轮实际节省0。
- [完整报告](../../agents/database/canonical-ddl-probe/report.md)、native-run1/2、native-summary、native-reference、net-budget和E seal可复核；当前8.0/其他8.4patch/OS未测，988真迁移/全CI未跑，不称兼容或验收通过。
- [Issue4阶段评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6399750242)已精确GET全文同；owner后续可另立完整性缺口任务。阶段封档，临时own服务全停，不扩大实验。
