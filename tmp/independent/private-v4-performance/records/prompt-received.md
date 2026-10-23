# 实际委托记录

本条由AI父协调/root实际发给全新fork_turns=none测试实例；不是学生手工操作，也不是本实例自造用户提示词演进。记录标识PV4-P001，独立实例任务/root/independent_performance_v4。

> 你是本项目全新无父会话的独立测试实例，本轮仅负责正式性能核查，不是开发/修复/白盒/全验收。工作根 /Users/yang/Desktop/nothing/软件开发大作业。当前阶段仅设计并冻结用例，尚未提供任何SUT，不许自己寻找产品版本。先读 records/acceptance/v4-performance-neutral-inputs.json（neutral packet在commit db12bfd4dab03e0b2614f354d8bd27a0e3616621）及其明确中性原始任务书、冻结v1.1规格/接口/DDL、运行协议；AGENTS工作规则适用。只依原始需求自己设计任务流转及查询、契约校验、升级通知接口三类正式性能用例，明确可复现数据准备/并发/预热与完整稳态/延迟、吞吐和失败统计口径、原数据与环境观测。不要读项目README状态、agents工作日志、提示词、开发/审核报告、任何以往独立轮次/用例/结果，不与其他agent联系。设计期不读/import Python/TS/Vue应用代码、不HTTP/SQL/Docker/浏览器/负载；运行协议明确允许的中性环境实现可为安全编排读取。为自己建独立worktree/codex/independent-harness-v4-performance分支，尽量positive sparse只物化中性材料和你的目录，不用root索引。真实测试脚本只放tmp/independent/private-v4-performance，已预留868/867/866（按需用，不凑数）；密钥只存本机私密ignored路径，接收证书可随H。必须先将真实案例/脚本/预期判据/输入hash/采样规则/数据计划/加密接收者冻结commit H，再只向我发表不含案例内容的freeze metadata（路径/哈希/精确H/范围）。开发/root不可读你的私密案例、内部清单、日志、输出、密钥、密文或解密结果；你只向root沟通，未明确发表不得供root查看。H后等待我另发准确SUT和运行绑定；不能自行把中性环境commit当被测源，不能提前执行。能力：独立hosted Linux MySQL8.4/RabbitMQ/API4workers/consumer/scanner/web、公开HTTP准备、SELECT-only观测、限期服务身份、显式只读runtime-metadata、加密取回；实际可用性由运行决定。完整限期到2026-10-24 01:43UTC，约2小时可用；不要为赶截止降低要求，完成不了如实记录未运行。需要额外中性能力只报约定，不泄私密案例。每阶段自己记录实际prompt/命令/失败，不构造学生参与。请现在仅完成设计与真实H冻结、发表metadata；用例细节不要发root。

## 本阶段明确新增的中性能力输入

PV4-N001：本实例只向/root提出固定六服务有界只读CPU/内存/网络/块I/O计数快照需求，未泄漏用例。父协调回复既有runtime-metadata不包含这些实际利用值，尚无新增可用性承诺；要求继续冻结、不访问SUT/其他轮次。

PV4-N002（实际父协调原文）：

> 已形成可供设计引用的中性接口合同 specs/changes/runtime-usage-snapshot-rfc.md（commit db7df7c1b7028f77c10046054d23d0bb7cf8de92）。它只涉及运维观察，不含SUT结果；可读取此明确新增中性材料。约定 control.py runtime-usage，无参数，六服务固定白名单，stdout单JSON schema_version1；0仅完整/非0不完整、字段unknown=null，准确字段/时间包围/稳定错误见RFC。计划Docker单次--no-stream/--no-trunc保留CPU百分比、Linux扣缓存内存、网络/块累计量及PIDs的CLI原单位字符串；这不提供RSS、不自动等于利用率/全程峰值/物理同机。当前仅设计，尚未实现或实测，不承诺已可调用；最终准确环境绑定会标注实际能力。你可按此冻结选择性观测；不需等待此补充才能制定原需求性能用例。

处理：只读取该明确中性RFC，将其hash纳入输入；仅在准确运行context声明能力时调用，未知/失败不推测零，不改变原性能阈值。
