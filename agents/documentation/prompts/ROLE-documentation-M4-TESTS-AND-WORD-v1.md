# ROLE-documentation-M4-TESTS-AND-WORD-v1

status used，实际发自/root，actor documentation AI。

## 实际派工原文

ROLE-documentation-M4-TESTS-AND-WORD-v1：开始下一轮，固定文档岗。根当前2e0481f（本地可merge准确SHA，稍后root推）；你自己的独立干净worktree/分支codex/，不要用根index。先核对AGENTS与documents技能（先前已使用仍遵从）。
1) 新建 reports/final/test-results-report.md，汇总准确版本的模块/真实依赖/完整CI/容器恢复/审核/独立v1/性能，明确“未通过最终验收”；335后端/0跳过、43文件2493/2818行88.47%+分支77.73%，前端24/307-333=92.19%均是0448fec，证据 records/ci/39945098961（原始95附件tar.gz与清单已保留）；同SHA容器恢复39945098943记录19表count/checksum相等。旧317/88.16历史保留，不混版本。独立公开两报告仅可读 reports/independent-tests/v1-blackbox-report.md/results.json（名字实际v1-blackbox-results.json），严禁跟随其私有证据路径或读tmp/independent；900分布340/183/328/49，183含歧义不能写183bug；38成功路径通过，3x400VU600s P95全部失败而吞吐/稳态零失败通过。IAT01开发修复650已合入但不是独立复测；02～05仍进行。UI独立补充未发布不能先引用。
2) 更新提交映射/AI证据材料的当前结果和R001人机归属，保留M0–M3原历史。C-P4审核限定关闭报告已合并；5886超786仍failure，方案估计不足，不假称规模达标。函数I/O索引若更新请锁准确本轮源码SHA，BE仍在修不要宣称未来源码匹配。冻结11文件不得改。
3) 形成可供学生审阅的本地Word技术材料：需规、概设详设、测试结果、AI可执行规格说明共4份，分别对应现有MD。本轮是准确截止版本的审阅材料，不伪装最终验收；学生研究正文绝不能代写。沿用本项目MD内容/8张已渲染真实图，不找通用模板。输出仅 .submission-private/review-documents/ 下（Git忽略），封面从 .submission-private/cover-info.json 0600取真实值，日期留空，不把具体姓名学号写公开日志/源文件。可复用的exporter放scripts/docs/（仅文档工具，禁止搬业务逻辑）。
4) DOCX首次create前严格调用一次mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 4 --output-format docx，必须成功后再author；root此前没有marker或DOCX。bundled Node/Python已由load_workspace_dependencies确定：/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node；.../dependencies/python/bin/python3。LO必须 /Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice，禁止用户桌面LO。使用skill render_docx.py，查看每份的每一页PNG、纠正后重渲染；完整QA前不得交付DOCX为合格。QA图片私密目录，不上传个人封面截图；公开QA只记录页数/摘要/缺陷与修订。请自行完成全部页面视觉检查，技术正文可有实际阶段范围与失败结论。
维护本岗日志/报告/handoff/实际提示词/真实Issue-PR对接并阶段commit/push，交准确SHA；若建新PR attach。需要问其他岗只问公开事实，禁止联系独立测试岗。无需重跑产品测试/压测；文档渲染可能有CPU负载，开始时告知root避免与后续性能诊断同时。

## 实际续条

- 后端IAT02至05 checkpoint479fc8f（生产3b6dab5）合入e62f753，55HTTP/SQLite开发回归，真实MySQL专项待CI；Word主体仍锁2e/0448，不反复追头。BE拟5至8分钟短跑期间不启动LO，等待root明确quiet结束。
- root102f2c9已发布独立UI补充，仅可读v1-ui-addendum.md/.json：原e8测3通过/1失败/1阻塞，原900不改；计数呈现缺失/空迭代观察与b485修复边界、深链blocked不扩大漏洞。不得跟私有证据或截图。
