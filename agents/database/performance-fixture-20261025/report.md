# 中性性能数据准备报告

数据库 AI。设计 `2f6c1f9` 先于工具 `d8addfdb24ee1c25c91b63bc6999e18619c231e0`，脚本SHA `c6167e799533e493ca9faa85241e1c0acecd92bf4b96c154c7ddc79a6be205df`。原始准备已完成，本次恢复仅封存文档/证据，无新SQL、数据库写入、构造重跑或测试。

## 范围与真实来源

只使用root明确授权的新schema/user `t44_p829_20261025`、127.0.0.1:13306、指定0600 application-env.json中的本库CRUD。未读取admin、其他库凭据、功能环境或独立测试资料，未执行DDL/drop/reset/全局设置，未启动API或请求HTTP。root先行迁移使用ade5的冻结schema字节；产品冻结源c8cea7e82805de5283ce67501769fa9a4efc1047，两者schema相同。迁移初始化来源与产品来源没有混写为一次全SUT执行。

工具复用冻结seed._populate及实际模板/规则，通过显式Collector接收行；生产seed无修改/monkeypatch。10份使用的生产源码/资源逐字核对c8，原seed SHA `c9d2a3382b1eeffa67f9ae757e87bf292eacbe97932c79e30f576366cbb40f93`。派生逻辑只在tmp/833，不移动业务代码降cloc。derived-helper.patch是设计父提交到d8新增helper的精确18768字节补丁，SHA `b789002a3d68881ee058cfda567ca9605c817983b33c9aa2183e4b4fb039d33f`。

## 实际库存与分布

2026-10-25 08:04:15.161936–08:04:21.609894 UTC完成唯一一次本库准备、提交及全量读取核验。原database-preparation.json为24899字节，SHA `e67af95b0ba78d2b3badc8e10138a4343197784feabaea7690466b1972ccca76`。18业务表写前全0；前后schema均18表/226列/0defect（另有root迁移技术表，不算业务表）。连接checkedout0并dispose。

|库存|实际数量|
|---|---:|
|projects / iterations|40 / 40|
|tasks / dependencies|6000 / 9000|
|reviews / decisions|11400 / 3600|
|原seed records口径|15000 = reviews + decisions|
|release_assessments，另计|3600|
|users / project_members|5 / 121|
|合成audit markers|40|

5个独立synthetic账号及实际id：m=1、d=2、d2=3、r=4、x=5。m/d/r在40项目角色1/2/4；d2只在P1为开发者且有capacity；x无项目成员。工具没有生成会话或token。

P1/I1包含800任务：400 distinct DEVELOPING、owner=d，end=anchor+72h；另400 disjoint PENDING active overdue、owner=d，end=anchor-48h。anchor固定 `2026-10-25T08:03:00+00:00`，两组均无依赖。其余5200任务轮转分配到39项目，各133或134，全部9000依赖位于这些普通项目，只指向同项目更小id且DELIVERED前驱，去重且无环。**这是明确集中偏斜，不是均匀/所有请求都带依赖的分布**。完整800个实际ID见原件actual_id_lists和单独中性public-inventory.json，不包含请求/验收用例。

任务关联的reviews、assessments、decisions.project_id同步重分配；高级状态、artifact、delivery/review/schedule版本和原批准内容沿冻结seed。写入按原循环FK顺序：tasks指针暂null，children插入后回填原指针。写前和提交后全量读回均检查35个FK定义涉及的记录引用、评审artifact/轮次/任务独立评审者、批准评审verdict、批准评估任务/id/version/schedule/delivery基线、两组状态/归属/计划、唯一依赖与DAG。没有把直接DB合成状态说成逐步走过业务流程的历史或真人批准。

## 复算与检查边界

seed44、anchor、实际actors、模板/规则原字节SHA和工具source都保留。源构造行logical SHA为 `05cd964a87a5438ab71cae8bad6f6284f83e2935e758e480002a64e63f1cd629`；离线与实际actor ids相同，两次逻辑构造摘要相同。该摘要覆盖builder逻辑行，**不含随机用户Argon2 hash、SQL服务器默认字段或整个物理库**，不能称整库字节可重现。

实际检查是一次离线构造/引用核验、两项预期拒绝guard、一次真实本库准备与后验；不是新增或重复8个锁工具用例。既有输出再次调用在O_EXCL处拒绝且原bytes/hash不变；非指定env调用在打开凭据/连接前拒绝，原失败JSON/stderr保留。两个guard的非零是预期门禁，不是产品失败；没有清库重跑，没有把重复检查累计为新独立通过。Ruff check和源暂存diff-check均0。

原08:04:21回执auth_sessions=0保持不改。root后来明确于08:15:44 UTC为5个合成用户签发5个actor_kind=1会话，本岗恢复封E时不再查询该库；这是后续环境身份准备事实，不是原后验错误，也不代表5个真人参加者。root说明该时点API仍未启动、业务库存不变，归于root提供事实，不冒充本岗新测量。

原始五文件逐字保留，见provenance.json/最终seal。提示词 ROLE-database-PERF-FIXTURE-20261025-v1真实记录AI操作者。Issue4按实际完成范围发表并单ID全文读回。当前只证明数据准备，不证明性能、功能、独立验收或规模达标。

[Issue4评论6395326771](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6395326771)由connector实际POST，随后精确单ID GET的完整body与本地稿逐字相同，原响应及hash见github-readback/verification。
