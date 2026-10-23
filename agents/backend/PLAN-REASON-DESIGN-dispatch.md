# Issue28本轮实际派工归档

实际发送者：总协调AI `/root`；实际执行者：后端AI `/root/backend`。原消息没有新的ROLE编号，本文档路径作为Prompt-Ref，不编造新编号。此设计不是用户新业务规则或学生亲自改码。

## 实际派工原文

A已由根核8原gzip哈希、437JUnit、43file覆盖分母并合入root982623381e9cfa1d6a7bad1de222e160503cbf08，精确源码与7584 byte等价；review1d6已合入、PR29 COMMENT真实。现在请新分支 codex/backend-plan-reason（独立旧A分支保持历史，自己的现有worktree干净可切），从根9826233开始，专门Issue28设计ONLY。结合前端已真实对话，定义：新schedule audit保存reason；旧audit读投影在证据充分时关联既有schedule_changes reason；缺失/歧义明确显示缺失不猜、不修改immutableaudit/no destructive migration/no new frozenAPI/code/field。须精确验证task/from/to versions、actor/time/完整beforeafter计划匹配的必要充分性、迭代批改场景/普通taskplan场景、2000字符与列表分页限制、一个bounded batch读取而非N+1、跨项目授权/非计划audit不污染、历史reason是否已经可见字段格式需要前端修改。先给自己真正设计提交+数据契约/新老样例、最小净LOC预算与红绿计划，根看后明确准入再生产实现，无须等用户。历史只读研究，不接触独立tmp/worktree，SQL如需真实只用自己t44_test合成fixture且描述动作；可静态先完成。维护本岗记录/实际prompt/GitHubIssue28对话/readback，阶段commit。全量CI/负载本阶段不跑、不反复计数。下一测试新文件若需要索号873起，883–874已预留新独立v3（不要读其内容）。

## 后续实际协调原文

收到，无任务批改的changeIteration保持历史说明。认可你先做设计/固定pairs数据库接口提案，不用N+1或IN交叉乘积+任意limit。请给DB owner明确需求（project_id+≤100个task_id/to_version元组、完整rows/仅参数化、硬上界/重复处理/排序、空集不查、异常/结果），勿在后端绕过Gateway或改DB。你设计commit后可释放槽，我会让数据库岗实现固定有限入口并返回；然后续派你接入/红绿。这是小技术对接由根决策，不等用户。原audit immutable/理由缺失不猜都保持。

纯Issue28设计/RFC/样例/离线schema验证记录可[skip ci]，保留8/8仅wire形状不是业务/DB/HTTP通过。提交/push后给根精确commit与RFC路径即可本阶段结束释放槽；我用新数据库岗实例接固定pairs接口方案。旧/database发不通如实记，勿当已确认。你本岗产品/测试/配置保持零变更，根按设计审查后续派接入。

## 真实交付与协商边界

- 只创建内部RFC、合成数据样例、离线形状/摘要记录及本岗日志/交接；生产、测试、配置、14冻结零修改。
- 只读Issue28/允许公开的v2阶段md报告及本方源码/规格；未读取独立私密材料/SQL现场/脚本或连接任何数据库。
- 正确当前frontend_logout已收到本轮设计范围；此前真实前端Issue评论6373191287/6373333383作为字段需求依据。没有指示前端本轮改码或测试。
- 尝试给历史/database发送固定pairs接口需求，工具返回`agent thread limit reached`，未送达；根明确将另启数据库岗实例，不视为DB已确认/实现。
- 静态查看manifest时误把files字典按索引0读取，实际KeyError:0已记在静态记录；修正为items遍历后继续。不是产品/业务/测试失败。
