# ROLE-reviewer-NEUTRAL-R30-20261029-v1

实际操作者：固定AI reviewer；仅与root对接；不是独立验收测试岗。

## 实际派工原文

接着做最小中性材料准备审核（无服务/云/会话执行）：后端新worktree .agent-worktrees/backend-neutral-r30 起点7374，阶段ffae5d84（UNVALIDATED，owner正补admin CLI+packet入口+本地fake验证，最终SHA随后root转）。当前19件，源码在agents/backend/neutral-r30/；请先审实际API造数与会话顺序/权限/窗口/源/包原件/独占对象/默认拒绝，尽快P1/P2，不等行政。root技术决定：全部源码镜像工具传输和infra检查ready后，签4个实际身份session，再用正常API做400create/start+400existing task事件/真实读回，最后密封新包（实际6400如实记）。issued/expires/首次完成UTC不伪写，grant前剩余TTL覆盖完整运行，绝不retime；默认false/null/TBD拒绝。0b产品不改，QA v2.4 core81e不改，旧V1不复用。

允许看已发表中性PUBLIC接口：/Users/yang/Desktop/nothing/软件开发大作业/tmp/772_independent_perf_20261029/PUBLIC/ 内 INTERFACE_0B_V24.md、NEUTRAL_0B_V24.template.json、IMPORT_RECEIPT_0B_V24.expected-shape.json、TARGET_0B_V24.json、GRANT_0B_V24.default-false.json、INTERFACE_0B_V24_FREEZE.json(e2d97c62eb4485a70a502594c5368586f81fbb808dd6c82169bebacccc97c976)、INTERFACE_0B_V24_CHECKS.json(1a6be2c1304bd9db87b98abc277b415ad4ce60f24b6ec7e2bb6e5d0286898614)，必要只读ADAPTER_0B_V24.py/ENTRY_0B_V24.sh。绝不读PRIVATE/REVIEW_R30_ONLY/未发布case。原source/bundle两manifest在rootcoord records/deployment/r30-backend-0b（已有校验）。newbudget9e...，APP idle6且scheduler另scope启动成7，不凭镜像数推实跑。

新审核小测试若需请用tmp/757_neutral_review_r30（此前新P1用了tmp760，数字不是全局顺序，不再扩大），只真实纯本地fixture/fake，不签实际token或HTTP。无产品/全CI重跑。最终owner仍改动时给你审核的精确SHA和未核diff，不抢改owner文件，不替root发grant。今天集中一次窗口，角色四件之后可简短封档。

## 实际执行范围与改进

- 从7374建立独立reviewer-neutral-r30树；未读取owner未提交admin/assemble等文件。阶段检查从Git精确读取ffae5d84源，避免owner继续修改污染原复现。
- 只读9个明确获准PUBLIC文件，核freeze/checks与逐文件hash；没有打开CORE_COMPATIBILITY、PRIVATE、REVIEW_R30_ONLY或未发布case。
- 用纯本地合成plan复现阶段目标image pin、origin/connect_ip、901秒窗口前置校验缺口；没有HTTP/会话动作。尝试fake login前缀时先遇到阶段http_primitives首行SyntaxError，保留原stderr，不冒作已完成该fake流程。
- 实质问题先发root；等准确最终SHA后仅核相关修复与新增入口，不代改owner、产品、QA core或grant。


## 最终复审派工原文

最终修复 producer 已推送 3be27131398a049f1a509918e5308f1bda7c8cec，manifest SHA 66ab164258803a8a62edfc3dbc713837431ce8b649664ab8de4c5a48a2359606。唯一运行改动 crypto_transport_proofs→cryptographic_transport_proofs；请与实际 GEN required16字段、wrapper最终8c73486440720506357ffa90efdb5b59cdd91028、原预算9e一起做准确SHA有限复审，给明确是否可进入一次云准备窗口，不以缺尚未开机才能有的 actual 证明无限HOLD。勿开云/读PRIVATE/SUT。今天19:00前服务器收尾，请尽快给范围化结论。

root另明确LOAD采用准确4f/8CPU/8GiB source-free standby作orchestration readiness，无HTTP/core import，正式driver前停；实际回执不冒完整工具/负载通过。实际执行只新增11项受影响链，先回root允许一次有限准备窗口，再补行政；不重跑旧case/fullCI。
