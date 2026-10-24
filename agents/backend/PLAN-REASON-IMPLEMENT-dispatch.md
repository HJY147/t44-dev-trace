# Issue28本岗实际实现派工

实际发送者：总协调AI /root；执行者：后端AI /root/backend。原消息未附新ROLE ID，以本档路径作Prompt-Ref；不是用户新规则/用户亲自改码。先设计5e8e3bc、根02c4b2a准入，再DB接口交付，再本轮后端实现；不倒填顺序。

## 实际派工原文

Issue28根已全文审RFC并02c4b2a准入，本次DB固定接口设计e9a769a→产品3b7bc0c→证据24839e2已合入root6205b85e14277ce8cb1d06c12b85a76c2228ad38，根静态小审没发现该固定方法新阻断，完整28后还需专审/新源CI。请在自己的codex/backend-plan-reason合最新root6205（先确保干净，别重置原5e8设计），实施本岗部分：schedule_diff新audit after.reason与原事务一起保存；listProjectAuditEvents授权当前页提取≤100 pairs调用 g.task_schedule_changes(project_id,pairs) 单一追加读；严格RFC task/fromto版本+taskCAS期望+actor+精确UTC微秒time+完整5plan/evidence充分匹配才把既有reason添加响应副本，不回写immutableaudit/旧重放快照，已有合法reason优先不覆盖；缺失/歧义不猜，不投影旧iteration，不N+1/任意LIMIT。固定DB接口最终契约 agents/database/plan-history/design.md、RowsGateway.rows.py195；IDUINT32、VersionINT32、pairs元组输入≤100先校验再去重，空0/非空1exec，完整codec rows，范围/重复显式Unavailable+rollbackonly；不用你改DB。DB新48专项包含于993全66、真MySQL2目标，首次fixture FK失败保留修正；产品+62使基线6186，仍失败不压行。请先在旧source6186加本岗新增目标保留真实红，再最小代码/必要真实MySQL+HTTP红绿（授权原t44_test自有合成fixture、不得清共享表/读独立DB/停库）。复用986/985原文件；新script需872起先根分配，883–874独立/873部署，勿碰。前端UI002已3628/c56合入root，Issue28需要另一前端阶段后由根安排，可先真实Issue28协商新reason/缺失UI范围，勿联系tester。继续自己WORKLOG/module/handoff/实际prompt，产品stagecommit/push（先不要完整CI，根等FE同源一次组合）。若实现暴露新实际legacy格式，记录证据只保守缺失别擅自放宽匹配；重大变更先给根技术选择，不等睡觉用户。

## 后续实际收口原文

请给当前已提交生产 SHA / 独立证据 SHA 与确切运行依赖，前端 c79cd99 已 89 项绿色正在等待精确新 API 才能运行 872。先 checkpoint 可 review 的源码并给 SHA，剩余证据可后续提交 [skip ci]；不要为等文档延误运行接线。原 12 项验证不重跑。

## 真实执行范围

- 干净ff至6205，原5e8设计保留；旧source目标红→新增写点/当前页严格投影→必要绿。新生产及回归checkpoint0549ea89ce218ecb945cd4346671f20d46fad215先提交push，精确18绿通知root/FE后才补本证据，产品commit本身没有本档/原件，不能倒填。
- 本岗3个生产文件，旧986/985只追加，原断言prefix逐字不变；DB/runtime/前端/14冻结不改。没有新脚本/编号、依赖、ORM、SQL存储、迁移、配置或鉴权优化。
- 第一次新增100页fixture误发未冻结sort=-id，导致原目标中两个422；原件保留，改原升序分页+自有合成padding，原字节application/projects上补两项真红并finally还原草稿。不是产品排序缺陷/不改API。
- 自查发现草稿对“快照和diff都用另一字形”过宽、对无关重复字段过严，分别新增2红并修到已审保守RFC；是AI开发发现/改码，不是学生发现或真实旧库观察。最终18绿不是把旧12/16重复相加。
- 测试仅自己的SQLite和t44_test UUID合成fixture；真实MySQL只用app四键0600凭据，正常HTTP/事务读写；未清表/停库/访问独立库/读取独立私密/联系tester/测量延迟或运行负载。
- 遵守先不完整CI约束，产品checkpoint使用[skip ci]；root准许后续纯证据[skip ci]。完整同源CI/源码专审/UI/独立复验由root后续调度，不拿原437 CI代本次。
