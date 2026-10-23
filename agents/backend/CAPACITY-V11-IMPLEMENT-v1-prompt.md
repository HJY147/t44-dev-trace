# 实际派工 ROLE-backend-CAPACITY-V11-IMPLEMENT-v1

来源：总协调 /root 实际消息，原文：

ROLE-backend-CAPACITY-V11-IMPLEMENT-v1：按人已采用、设计先审的顺序实施v1.1。根当前eac253039cd85873d3b262e648b2b74d94d715a8，已含你652工具记录、FE f654、M4 Word QA、D005/D006与reviewer设计证据d7c46a6；先在你独立干净worktree merge此明确SHA。读 records/decisions/D005.../D006...、U015/U016和 specs/changes/capacity-lifecycle-v1.1.md（最终RFC bbc4be6，hash a6271ef7f6180c29b7aa3e0bfa373b25b76fbf19f1d11233768388d495682d98）、reports/reviews/capacity-v11-design-bbc4be681f19a386fbca40baf97a63ab902b3f89.md。限定设计可准入实现，不是最终通过。
业务：现有createTask匹配capacity保留；待受理/blocked-from-pending转派须接手人有效developer且登记在同迭代capacity；changeIteration新capacity必须含本迭代全部状态1–5任务owner（查全量，不只old-new移除名单）；6/7可移出容量；action9返工重新核有效人力+capacity才可激活。原项目成员/开发角色保护1–5+7不放宽，原D002不允许开发后转派不变，不加预算耗尽/工时分配算法。只复用现有CAPACITY_REFERENCE_INVALID，assignment与rework补422操作声明，原角色/版本/状态/幂等顺序和成功/拒绝事务保持。
并发：assignment加入项目行锁，与create/changeIteration/rework统一session/idem→project→有序成员→有序task，不另开事务提前提交；竞争移除拟接手人 vs转派/创建/返工不能留下active owner缺capacity，合法转派完成后移除原owner可依次成功，不能把所有不同资源安全更新都限定仅一成功。
本轮授权你修改 backend/t44及已有986/985必要回归、权威 specs/contracts/openapi.json/README.md与后端运行副本，同时在specs/backend-design.md明确新锁/守卫设计（保留原v1历史）；info.version和Meta.contract_version.const同步1.1.0，路径仍/api/v1、38操作、DDL18/226不改。前端直接导入权威源，请核对现有版本fixture/断言，跨前端文件先向FE岗提需求由其执行。DB岗会单独更新field-dictionary与persistence-contract，不覆盖这两份；root更新business-rules/requirements/AGENTS并最终建立v1.1父链freeze，你不要改records/spec-freezes/v1.json或倒填旧11hash。旧v1可从ae60dc3恢复，当前文件变更是显式新版本，不声称旧11仍当前逐字相同。
先补有意义的新版行为/竞态回归，再代码/真MySQL专项与全套CI必要检查；版本变更的机械fixture修订说清楚、不删原业务断言。不碰tester库/脚本/私有材料，不联系tester；新脚本需向root申请tmp编号next954，尽量在既有986/985追加。保留原失败及真实GitHub Issue/PR交流，维护本岗日志/报告/handoff/实际prompt，阶段commit/push准确SHA。
先完成这次业务变更，性能短诊断暂不同时启动；docs已结束LO、FE真实浏览器刚结束正在归档，无需重跑你362已绿旧源。955回环直连修复未验证的历史保持，后续单独协调新窗口。

## 实际续派：先合同冻结再业务实现

执行顺序再收紧以满足任务书“接口先冻结”：请先交第一checkpoint只含权威OpenAPI1.1/后端运行副本/README/backend-design（可含基于RFC准备的新回归及改前失败，但业务守卫生产实现暂缓），不要把契约和新业务实现混成第一commit。DB岗正在先交2份存储规格，root更新business-rules/requirements/AGENTS；这些合同/设计合并后root先生成单独v1.1父链冻结清单并通知你，再继续实际守卫/锁/回归实现。你的新测试可先按已审RFC设计，不需要等人再问；正式新业务代码等新合同freeze后，旧v1清单不改。若已开始改业务，请保留未提交草稿但先选择性提交合同部分，明确其尚未实现/未部署。
