为中小外包团队提供迭代排期、交付任务七状态、证据评审、上线风险与回滚决策、延期升级和审计追踪。1.1新增已获用户采用的人力规则：创建/允许状态下转派需当前迭代工时；状态1–5负责人不得移出工时安排，6/7可移出，7返工前先恢复有效人力。项目成员保护和原转派边界保留。

Vue3/TypeScript + FastAPI + MySQL8.4 + RabbitMQ + APScheduler + Compose，38操作。需规、设计、契约先经限定审核，再于189dc4a独立冻结1.1，旧1.0及历史测试保留。11个AI岗位按阶段自行提交、Issue/PR对接，独立验收实例fork_turns=none；共享文件系统的流程隔离边界如实记录。

| 验证 | 已有证据与边界 |
| --- | --- |
| 精确4c20f32 CI | [run39958165108](https://github.com/HJY147/t44-dev-trace/actions/runs/39958165108)四job成功；后端394项、0失败/0跳过；全43文件行2542/2865=88.73%，分支78.55%。[原失败与修复证据](https://github.com/HJY147/t44-dev-trace/blob/415d090b3fd2345b1ad7859ae26e7b2b0299bf47/agents/backend/capacity-v11-ci-summary.json)保留，不算独立复测 |
| 前端实浏览器 | f654的27项CI、92.79%行覆盖及80真实HTTP；未读/未处理1/1→1/0→0/0，任务状态/版本不变。1.1机械fixture另同步，未倒填1.0浏览器证据 |
| 容器/恢复 | 0448的[真实Linux演练](https://github.com/HJY147/t44-dev-trace/actions/runs/39945098943)，4workers、隔离恢复19表行数/checksum一致；非租用云服务器。新中性独立验收环境仍在能力复验，未运行harness |
| 独立验收 | 原e8[报告](https://github.com/HJY147/t44-dev-trace/blob/415d090b3fd2345b1ad7859ae26e7b2b0299bf47/reports/independent-tests/v1-blackbox-report.md)未通过；三类400VU/600s P95为3035/1908/5506ms，均超过270ms。新实例只基于[中性输入](https://github.com/HJY147/t44-dev-trace/blob/415d090b3fd2345b1ad7859ae26e7b2b0299bf47/records/acceptance/v2-neutral-inputs.json)设计冻结用例，尚未接触SUT |
| 规模 | [5973行](https://github.com/HJY147/t44-dev-trace/blob/415d090b3fd2345b1ad7859ae26e7b2b0299bf47/records/metrics/source-count-v11.json)，超过5100上限873；原统计口径不改，SQL解析库POC未准入生产，实际节省0 |
| 报告 | 四份本地技术Word共28页已逐页QA；有明确M4内容cutoff，最终1.1与验收结果仍需更新。研究正文由学生本人写，R001原话与AI材料分别保存 |

仍需：性能诊断及有效优化、规模达标、新实例独立执行与完整新SHA审核、最终技术文档更新，以及学生本人研究报告和真实人工操作证据。此PR保持draft，不发布reviewer/stage成功、不绕过main保护、不合并未通过的完整产品。
