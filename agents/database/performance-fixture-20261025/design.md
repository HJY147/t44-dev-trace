# 中性性能数据准备设计（不是验收用例）

root本轮明确授权：新schema/user t44_p829_20261025，127.0.0.1:13306，仅指定application-env.json内本库CRUD；19表冻结迁移已由root完成。本岗不执行DDL、drop/reset/global，不读取其他env/admin/功能库/独立测试目录，不触发HTTP/独立用例。生产冻结c8cea7e82805de5283ce67501769fa9a4efc1047，schema及seed与ade5同字节；初始化迁移源与产品运行源分别记录。

复用冻结seed._populate，以显式内存Collector接收其insert_many/update_many，不monkeypatch或改生产seed。显式变换仅写tmp/833 helper：挑400现有DEVELOPING和400现有PENDING（都无评审/批准指针）集中P1/I1、owner=d；前者end=anchor+72h，后者end=anchor-48h，start=anchor-4d。其余5200按39项目轮转，明确800/5200偏斜，不称均匀。高级任务状态、版本、reviewcycle、artifact、review/assessment/decision内容沿原seed，project_id随task一同迁移。

40projects/6000tasks/9000edges；records按原seed为11400reviews+3600decisions=15000，另3600assessments，不把三者合计18600写15000。新依赖只在非压力项目内，指向同项目更小id且DELIVERED任务，去重/无环，压力两组均无依赖。5独立synthetic用户m,d,d2,r,x；m/d/r在各项目角色1/2/4，d2在P1角色2并登记capacity，x无项目成员，仅中性账号；root自行签5会话，本岗不创建token/session。

执行前：核工具commit/源hash、冻结seed/Rows/schema/UoW/engine/codecs/resource字节、appenv0600和精确host/port/db/user、SELECT DATABASE、check_schema、全部18业务表为空。只在本库一个UoW内创建5用户与批量写入，失败rollback，CommitUncertain不重试；不清数据。循环FK任务指针按原seed先null插入children再update。

写前内存核counts、项目分布、两组disjoint/state/owner/plan、全部FK外键（通用metadata逐项匹配）、版本/轮次/批准指针及图前驱。写后同库读回counts/全表FK反连接/两组实际IDs与字段、版本/引用，一致后才写成功metadata。schema检查源与product源分开，声明直接synthetic不冒充逐步业务历史。

输出只公开中性库存/ID/provenance/anchor/seed/config hash/logical content hash，不含DSN/password/hash/token或自由业务正文。输出O_EXCL|O_NOFOLLOW固定fd，原失败保留。仅必要本地内存guard后一次本库准备，不读取tmp/829或任何独立case。本轮若超时/失败，报告准确未执行/失败，不降低库存/FK要求。
