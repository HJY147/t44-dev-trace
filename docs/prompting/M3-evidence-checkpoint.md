# M3 AI 使用留痕事实 checkpoint

本材料由提示词岗 AI 整理，供学生自行选择事实和撰写研究报告；不是学生本人研究报告，也不使用第一人称代述其收获。基线为公开提交 `8fb74cdf893d83413338f966156274fe58caf22b`，另标明后端 `64b4f891ee77eeb2b1054c3a40af084eb6691d5c` 的增量来源。后续变更须另核对，不将此快照称为总验收。

本轮仅文档/Git/远端只读取证，没有本机测试、构建、渲染或业务请求；未联系独立测试，未读取未发布的黑盒资料。来源摘要与远端回执见 `M3-source-manifest.json`，实际问取与回复见 `M3-source-inquiries.md`。

## 用户原话、AI 动作与人决定

| 来源 | 可确认归属与作用 | 不得改写为 |
| --- | --- | --- |
| U001 | 用户提出固定多岗位、独立测试无开发上下文、各岗记录及提示词岗 | AI 岗位是学生本人、已杜绝作弊、已量化提效 |
| U002 + U003 | 用户提出建仓/clone、阶段 commit、GitHub 对接和审核；补充公开开源 | 每个 commit 都由学生亲手完成或不同账号真人审核 |
| U004 → D001 | 用户回复“采用这套规则，继续设计和开发”，采用 AI 提出的业务规则 | 用户亲自编写状态机或执行生产回滚 |
| U006 → D004 | 用户回复“采用推荐方案，继续开发”，采用字段/错误码取舍 | 用户亲改实现、用户本人发现设计问题 |
| U010 | 课堂要求过程研究报告本人写；同一原文也表达希望提示词岗代作本人 | 把提示词岗变成人类作者；AI 可整理事实素材，不能改变真实作者和经历 |
| U011/U012 | 用户要求开发前需规/设计、开发中持续补充、多画图 | M2/M3 后补的图早在编码前已全部存在 |
| U013/U014 | 用户提到不确定名称的“AI逆向一切”工具 | 已确认某工具/标准、可预判老师评分；本轮没有额外调研或规避评判 |

U001/U002 原文保持不动，优化稿 U001-O1/U002-O1 仍为 proposed。ROOT-documentation-M3-DIAGRAMS-v1 文件已明确“事后重述”，本轮如实归类为 retrospective_goal，不计作实际接收的派工版本。

## 从需求审查到设计的实际推导

| 步骤与真实输入 | 产物/反馈 | 可核对版本与边界 |
| --- | --- | --- |
| T44 约束 + U004/D001 采用规则 | requirements/business-rules、状态出口与阻塞/延期/回滚依据 | D001 明确规则提出者 AI、采用者用户；不冒充改码 |
| ROLE-backend-CONTRACT-v1 + 数据库 DESIGN-v1 | OpenAPI、backend-design、DDL/字典草案 | 后端 `b893353c9bcf45e833f70f56bf6f72025f611271`；整合待审 `717cd65ef73560fde7ff5bca2821c9fe2b20d68a` |
| reviewer DESIGN-v1 审精确 717cd65 | C1 原请求 ID 持久来源、C2 收件人上限、C3 时间域、C4 不可能错误分支，结论不通过 | [实际审核 Issue](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6358801740)；不能被“规范能解析”覆盖 |
| ROLE-backend-CONTRACT-v2 / 数据库 DESIGN-v2 | 定向改 C2/C3/C4，补 response_request_id/COMPLETE 约束 | 后端 `72c6c0064e52cb091e8ca4533a1cb862fc46866d`；数据库 `2ca79af796bf17aed6a2e76de75545623c0d0566`；[后端实答](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6358981840) |
| 新版本技术复审 + U006/D004 采用 | v1 契约/DDL 冻结 | `ae60dc37fdaefecaca33e734a354add6ba9ebe29`，`records/spec-freezes/v1.json`；不是产品验收 |
| 各岗 APPLICATION/INTEGRATION 实际派工 | 完整实现、模块与真实集成记录 | 阶段和验证环境分别记录，不能把不同模块数量相加作总验收 |
| ROLE-documentation-M2-QUALITY-v1 + U010–U012 | 需求组织、概设详设、FR 追踪、7 图、研究事实材料及自写模板 | `agents/documentation/prompts/ROLE-documentation-M2-QUALITY-v1.md`；保留历史提交，不倒填开发前成稿 |
| 审核指出文档关系/重试/时钟差异 + U012 | M3 8 图与语义修正 | `8fb74cdf…`、`docs/reports/M3-diagrams.md`；事后目标重述与实际修改记录分开，未做本轮渲染 |

## 同一任务的真实 prompt 族

| 族/目标 | 实际记录与反馈推进 | 本轮计数结论 |
| --- | --- | --- |
| 后端接口设计修订 | CONTRACT-v1 → 精确 717cd65 审核失败 → CONTRACT-v2 定向修订，正文在 `agents/backend/CONTRACT-{v1,v2}-prompt.md` | 两个有实际输入、失败反馈和结果的版本；不足六版 |
| 前端完整集成与审核缺陷修复 | INTEGRATION-v1 初始任务 → 958 编号协调 → reviewer 正式 C-P1/P2 反馈后优先最小修复 → 新通知数据准备/专用身份/避免重复事件的后续输入 | 同一任务的实际续派均保存于 `records/prompts/ROLE-frontend-INTEGRATION-v1.md`；编号/身份/数据准备是协调续条，不自动当成独立优化版本 |
| 设计复审 | reviewer DESIGN-v1 → 修复后 DESIGN-v2 | 同一审核目的、不同指定 SHA 的两轮；不是六版 |
| 产品精简 | 后端 REFACTOR-v1 → 729344e 真实 CI 失败 → 总协调转交失败、后端 64b4f89 修复 | 后续反馈有原始 CI；暂未找到单独逐字修订 prompt 快照，不臆造“v2” |
| M1/M2/M3 文档 | REPORTS-DRAFT-v1 → 实际 M2-QUALITY-v1；M3 文件明确为事后目标重述 | 阶段扩充与事后记录分列，不构成已核实六次执行演进 |

十一个岗位的 M0 不是一个 prompt 的十一版；CONTRACT、CORE-FOUNDATION、APPLICATION、INTEGRATION、REFACTOR 也不能只因同属后端就算同一任务六版。**本轮尚未核实任何一个满足六版真实演进证据的单一族，不能宣称达标。** 后续只补已经实际发生的输入、反馈和结果，不制造无意义改写。

## prompt → 结果 → 审查 → 修正（均为 AI/工具事实）

| 映射 | 输入/上下文 | 已发生问题与修正 | 证据、操作者与验证限制 |
| --- | --- | --- | --- |
| A1 设计的时间/收件人/错误域 | CONTRACT-v1，717cd65 | 语义设计失败后 CONTRACT-v2 修正，而非只让 OpenAPI 能解析 | `contract-v2-before-fix.log`：90 失败；`contract-v2-validation.log`：1130 设计检查。识别：审核 AI；修改：后端 AI；不是 HTTP |
| A2 幂等请求 ID 持久来源 | D001/首次设计审核 C1 | 用 response_request_id 保存最终所存结果来源，COMPLETE 非空 | 数据库 DESIGN-v2 / 2ca79af；后端同步说明。识别：审核 AI；修订：DB/后端 AI，不计人工校正 |
| A3 C-P1 Iteration.plan | 前端集成 + 真实冻结嵌套响应 | 错扁平夹具掩盖 plan 预填/名称错误；改读 record.plan/i.plan.name 并约束夹具 | [e01 失败报告](../../reports/reviews/product-v1-e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef.md)、`88e7df805c37824ac1b6b2ed2813e01504481156`、integration-ui-regression-before。识别：reviewer AI；修复：frontend AI |
| A4 C-P2 历史快照冒充当前 | D001 重放快照边界 + 正式反馈 | 先刷新后仍说“任务现为”；改为历史结果说明、以当前详情为准 | reviewer 959 两条原失败与同一 88e7df8；原断言未弱化。显式 mock 组件复现不是独立验收 |
| A5 C-P3 规模与真实冗余 | 原政策 3500–5100 + INTEGRATION-v1 | e01 原 cloc 5944，真实删除 83 条未消费 CSS，styles 297→214 | `bfa1625ac40df4eed0648ab629c5778bf47490cc`、integration-css-removal.json；识别/核实/修改均 AI。删 83 不等于整体已达标 |
| A6 通知读与处理的真实边界 | 同族后续新任务授权，不重置旧通知 | 原通知不可重复“造未读”；新任务/event173，分开验证 read/handling，保留 drawer/响应式等失败 | `b485279909720dac0adf1fb1bfbe9b23ef35dd39`、integration-notifications-complete；最终 114 HTTP 是前端 AI 既有只读复查，原写运行并非 exit0，不是本岗执行 |
| A7 文档 ER/事务/时钟 | M2 + reviewer 对 Runtime/Scanner 的核对 | outbox 可选 task；503 后调用者原 key 重试；cutoff 选候选、当前 clock 判级 | M3-diagrams、8fb74cdf；修改者总协调 AI。8 图源/成图 hash 不代表最终 Word 逐页 QA |
| A8 C-P4 Schema 漂移漏检 | PRODUCT-v1/冻结 DDL | 原 checker 只比约束名，957 改索引/FK/CHECK 语义仍 passed | e01 failure 和 957-schema-probe.log；识别 reviewer AI。DB 增量修复尚需责任岗/新 SHA 验证，不声称真实 MySQL 已漂移或已修复通过 |
| A9 后端减量后符号遮蔽 | REFACTOR-v1 | 729344e 的 cmd/局部 commands 重名造成真实 CI 失败；64b4f89 修复并继续共享创建/会话逻辑 | backend 回复 + 64b4f89 中原 `refactor-ci-39937742613-failed.log`；root/后端 AI 与 CI 发现，不是用户亲自 debug，后续指定 64b4f89 的远端 CI 已核对成功，见下段；并非本机复跑 |

**317 全绿并未阻止随后审出问题。** e01 审核复核的是 265d89b/run39931640641 的既有 317 pass/0 skip 原件，不是本岗重跑；reviewer 随后仍用真实组件/Inspector 复现 C-P1/P2/P4，并按原口径发现 C-P3。e01 的 `reviewer/stage=failure` 和[公开结论](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6362426845)保留。缺陷修复提交存在，不等于新 HEAD 已审核放行、正式性能结束或独立验收通过。

## 最新指定 SHA 的远端 CI 与质量范围

FE `b485279…` 的 [run39937368245](https://github.com/HJY147/t44-dev-trace/actions/runs/39937368245)、BE `64b4f89…` 的 [run39938619826](https://github.com/HJY147/t44-dev-trace/actions/runs/39938619826) 均已远端回读：static/contracts/frontend/coverage 四 job success，coverage 原日志均为 317 passed。BE 的 JUnit 与覆盖率原件另在 `3ee07251a5179208d720235e699a6855f46e8c8c` 归档，实际修复源仍是 64b4f89，不能把证据提交 SHA 当成被测源码 SHA。

BE 后端真实回复给出 JUnit 317、0失败/错误/跳过及行覆盖 2406/2729=88.1642%；CLI 含分支 TOTAL 85.74% 是不同口径，不混写成纯行覆盖。元数据、原日志摘要、原 SHA-256 以及脱敏副本在 `docs/prompting/evidence/gha-*.json`。副本删掉凭据赋值/连接信息相关行，明确非逐字原件；远端原件来源保留。

这些支持“指定修复源通过其远端开发回归”“既有审核发现了绿测未覆盖的真实缺陷”，不支持测量工作时间节省、缺陷率下降或将单次修复当总体质量因果证明。独立验收、性能、规模和新 SHA 审核继续分别待证。

## 真实缺口，不以 AI 记录顶替

| 提交要求 | 本轮可核实的人类证据 | 缺口与下一步 |
| --- | --- | --- |
| 同一 prompt 至少六版演进 | 尚无单一族达到六个有真实修订依据和执行结果的版本 | 未达标；继续收真实版本，不按岗位数凑 |
| ≥12 条人工修改对照 | 本轮 0 条可归为学生本人亲手改代码；已收 AI 修复另列 | 至少缺 12 条可核对作者、前后 diff、理由和验证的真实人工记录；现有 AI 代码不改标签 |
| ≥3 条人工识别与纠正幻觉 | 本轮 0 条可归为学生本人识别；审核 AI/CI 找出的错误单列 | 至少缺 3 条真实人工识别证据；普通 bug 不自动等同幻觉，不能抄任务书例子或补写识别经历 |
| ≥5 处上下文到最终代码且说明人工校正 | 已给 9 条 AI/工具事实素材；其中 0 条具有用户亲自校正证据 | 至少缺 5 处符合人工归属的实际映射；最终代码 SHA 变化还须重新核对 |
| 学生研究正文、个人收获/课程建议 | 原文要求与 AI 材料/自写模板存在，尚无学生本人最终成稿证据 | 学生自行写、核对事实；本岗不代作经历或署名 |
| 新 SHA 审核/规模/性能/独立验收 | e01 失败明确；本轮未收新的全量放行或明确发布独立最终报告 | 继续按版本和范围保留待办；不读未发布内容，不以“CI绿/图已画”替代 |

这些数字是**本轮已收材料能确认的数量**，并非断言学生在其他地方从未做过。若学生补充实际本人操作的原始记录，再核对来源与版本；不要求其编造历史或事后把 AI 行为归到自己名下。

## 给本人自写的事实选择提纲

可自行回答：选择 U001/U002 时希望解决什么协作问题；对 D001/D004 为什么采用；“能解析”与“语义正确”、错夹具与高覆盖、旧快照与当前事实的差异如何理解；看到 e01 failure 后哪些决策必须由人承担；还有哪些证据缺口无法用 AI 生成填补。答案和个人观点由学生本人形成。本页仅给问题与来源，不替其完成正文。
