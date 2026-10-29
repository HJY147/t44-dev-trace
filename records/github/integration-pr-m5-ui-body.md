为中小外包团队提供迭代排期、七状态交付任务、证据评审、发布/回滚、延期升级和审计追踪。1.1使创建/允许状态下转派必须有当前迭代工时，状态1–5的负责人不能移出工时安排，6/7可以移出，7返工须先恢复有效人力。原项目成员保护和转派边界保留。

Vue3/TypeScript、FastAPI、MySQL、RabbitMQ、APScheduler与Compose共38操作。需求和设计经限定审查后独立冻结1.1，原1.0父链保留。新增米咖玻璃UI按用户要求先提交OpenDesign官方本地技能/模板原型326f971，再导入840b1a8；实际浏览器发现的既存空文本强转true另以设计7369400→修复75c3468→证据6212e5f留痕，不混成视觉改动。

| 验证 | 精确证据与边界 |
| --- | --- |
| 后端 | [5dcb精确源CI](https://github.com/HJY147/t44-dev-trace/actions/runs/39970988113)412项，0失败/错误/跳过；43文件行2550/2872=88.7883%，排除0。只读契约校验改为单UoW，查询减少不等于P95通过；[限定审核](https://github.com/HJY147/t44-dev-trace/blob/6ba9f94ad23ac96380269aaefa8726f8b535b450/reports/reviews/read-uow-5dcb73cc10c38deb14fae68d33318b04d538fecf.md)不替代整体验收 |
| 前端 | [视觉阶段](https://github.com/HJY147/t44-dev-trace/blob/6ba9f94ad23ac96380269aaefa8726f8b535b450/agents/frontend/warm-glass-validation.json)27测试、92.81%行覆盖，1440/390实浏览器18图；[初值修复](https://github.com/HJY147/t44-dev-trace/blob/6ba9f94ad23ac96380269aaefa8726f8b535b450/agents/frontend/empty-value-validation.json)保留红→绿、14项定向与4图。新组合源CI仍在运行，未套用旧全量结果 |
| 独立验收 | 仅[4c的v2 API阶段报告](https://github.com/HJY147/t44-dev-trace/blob/6ba9f94ad23ac96380269aaefa8726f8b535b450/reports/independent-tests/v2-api-stage-report.md)已明确发布：38操作有成功响应、1596次响应Schema观察，未完成全错误语义/副作用审计；剩余故障/UI/性能/白盒未据此判通过。独立实例无父历史，先冻结案例；私密资料未交开发侧 |
| 容器/恢复 | 旧0448的Linux四worker备份恢复演练保留。新[f118环境能力核验](https://github.com/HJY147/t44-dev-trace/actions/runs/39977039692)有真实逐次恢复JSON、MQ元数据和合成加密传输，但harness=false，不是独立fault验收或租用云服务器部署 |
| 性能与规模 | 原独立v1三类400VU/600秒P95为3035/1908/5506ms，均超过270ms；无新正式通过。当前[6051有效源码行](https://github.com/HJY147/t44-dev-trace/blob/6ba9f94ad23ac96380269aaefa8726f8b535b450/records/metrics/source-count-empty-text-fix.json)超5100上限951，原cloc口径不改，未准入原型实际节省0 |
| 文档与留痕 | 11岗位阶段提交、Issue/PR协作及独立审核。M4四份私密Word共28页已视觉QA但内容cutoff明确；M5需求/概要/详细设计、图和过程更新进行中。R001思考、R002课程建议为本人原话，AI材料另记，学生本人最终研究正文与真实人工操作证据仍未齐 |

仍需满足性能/规模门槛，完成剩余独立验收与精确新源审核，更新最终技术交付并由学生亲写研究报告。本PR保持draft，不发布reviewer/stage成功，不绕过main保护，不合并未通过的完整产品。
