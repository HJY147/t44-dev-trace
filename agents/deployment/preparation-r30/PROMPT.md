# ROLE-deployment-PREPARATION-R30-v1

来源：root 给固定部署AI的真实派工，非独立测试提示词，非学生手写。本文件记录实际使用版本；未制造建议版或迭代计数。

## 原始派工（原文）

你是用户明确要求的固定部署岗，R30仅免费/本地准备，禁止启动/购买/修改云实例，禁止任何新费用。工作目录只 /Users/yang/Desktop/nothing/软件开发大作业；先读AGENTS。以root7374b3637b06465d448fc2e81952ba18fc676315建 .agent-worktrees/deployment-preparation-r30 / codex/deployment-preparation-r30。当前受审产品源0bffe0c535e5897890aebf30879fdd3839dc52d6，原生CI40827655008四job成功（796BE/89FE）；应用5880仍超780。两原VM APP i-bp13uag4r4u9r2hge0mt(64vCPU/128GiB)、LOAD i-bp13uag4r4u9r2hge0mu(16/32)已节省停机保盘，auto-release-在04:59详情核；06:18列表仍STOP/节省。原云产品f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f、旧短测400P95343–636ms未达；QA772旧cloudNP无runtime不改。现独立工具v2.4只在本地模拟完整E2E/认证通过、Linux通用子集4CPU host/2CPUquota通过；原LOAD Python image sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1、Python3.12.15/完整8CPU Linux工具尚未再验。不能称SUT性能达标。

任务：检查并形成下一次有限云窗口的准确0b镜像/源码/传输/部署准备，可用免费公开GitHubActions构建，但不启云，不接触独立测试PRIVATE或未公开case，不联系测试岗。只读已明确发表的PUBLIC元数据，不读 .runtime 下旧账号/密钥/session私件（新会话必须就绪后另发）。原公开运维工具在 tmp/790_backend_contrast_20261028/p64-f7-window1600/ 以及agents/deployment/resume-20261028/及相关公开runbook中；这些旧f7源/硬截止/窗口包绝不能直接复用或改时间后重放。请检查当前workflow/工具能力，为准确0b和新的隔离run/source/image/manifest出可审查新一版准备；四角色真实sessions/TTL需所有传输解封、运行前检查通过后才签发，旧expired包不能重用。尽量利用原双机已缓存且有内容证明的官方镜像，只需准备新backend准确image，不重复搬运全部500MB镜像；不要靠给旧镜像改标签冒充新源。任何新生成source包/镜像都要官方来源/层与源文件bytes/hash证明，错误/缺项直接拒绝。

先给有依据的准备审计和明确文件/命令/缺口，随后可实现必要本地工具及有意义的边界测试（新测试建议tmp/761_deployment_preparation_r30，先查占用保持递减），可免费GitHub构建并核artifact。部署栈、冻结契约、应用代码不改；跨owner需求只发root。保留所有首次失败，不假称image/预检/派发等于验收。输出一个具体可审核runbook：boot前ready清单、预计实际云步骤、硬时间界限/主动封存与可恢复节省停机阶段；费用紧张，下一窗口应尽量30–45分钟完成并保盘停机，不以删除数据省事。最终是否启云由root在准备和QA准入后决定，不问用户重复授权。四件/真实prompt/证据/阶段commit和GitHub issue/PR留痕。尽快先给缺口和最短可行路径，不要只写泛泛计划。

## root 实际追加准入

收到首轮实核。准入优先新增backend-only准确0b source/image免费构建路线，避免扩张旧935 derivation的语义；只准备新backend，原APP其它官方cache开机后再只读复核。若源替换器路径更短，必须单独新版本明确当前0b全53文件actual bytes/hash，schema.py变更来自已审38d11/7b15，DDL原字节/hash不变；新镜像需真实新构建或明确“已证明基镜像+0b只读源码”运行来源，不能给旧镜像贴0b标签。所有已声明frozen对比差异要逐个如实列，不绕检查。给出两路径传输量/工作量实际依据后自己选最简单可审实现，不要同时造两整套；需把源、依赖base、镜像config/layers分开出证明。无云操作、无新会话/旧grant重放，应用源保持0b；免费CI可执行，镜像artifact就绪才考虑boot。另root本地完整工具v2.4已公开authenticated PASS（仅本地模拟）及Linux generic subset报告，PUBLIC元数据允许看但不读PRIVATE；这不等于正式Linux全执行器或SUT通过。

## 使用理由与产物

旧frozen拒绝是事实；新scope明确精确源与唯一已发表schema实现差异，避免放宽旧检查。此实际版本对应AUDIT、backend-only工具/workflow、tmp761边界和下一窗口RUNBOOK。原始用户完整请求由root保留，本岗不把root派工改称用户原话。
