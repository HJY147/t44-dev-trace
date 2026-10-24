# 实际派工 ROLE-scheduler-FOUNDATION-v1

来源：总协调实际消息；实际操作者为 scheduler AI，非优化版替代原文。

开始ROLE-scheduler-FOUNDATION-v1真实代码阶段（覆盖初始化TASK只做设计限制）。用户已采用D001业务规则；Q002字段/错误码仍待人的选择，不做业务API/项目DDL/DB扫描联调。请自建.agent-worktrees/scheduler，分支codex/scheduler-core，base当前c5c14aa，使用自己worktree索引。读root AGENTS、specs/business-rules.md、implementation-layout、specs/human-review.md，现有backend hash依赖锁只读在.agent-worktrees/backend/backend/requirements.lock，Python3.12/uv路径见协作资料，不改共享锁。可写 backend/t44/scheduling/、backend/t44/resources/escalation-rules.json、backend/tests/scheduling/及本岗日志/报告/handoff/prompt。本轮实现两件可复用基础：1）从JSON加载并校验版本化三级提醒规则，纯函数按now-planned_end计算最高当前窗口，24h前临期/超期<24h/超期>=24h，UTC-aware、<=6微秒有效支持1000/9999边界，避免end+24h溢出；只返回内部窗口判定，不假装已持久去重/发通知。规则不硬编码在UI；按D001默认真正可用，不伪造人的技术审批。2）APScheduler3单独进程可注入scan callback的构造/生命周期基础（UTC、60s、coalesce、max_instances=1，API多worker无副作用），不要创建伪成功空CLI/真实DB扫描；正式入口后续接入。查当前官方APScheduler文档再实现，真实模块单测覆盖边界、非法config、最高level和同刻确定性及生命周期；仅模块覆盖率明确范围，不称全产品80或独立验收。给出真实扫描/幂等后续接口约定与复杂度说明，但当前DB去重未实现如实写。原命令失败保留并处理，必要自测一次通过后不刷次数。自己显式commit/push，draft PR base codex/team-bootstrap并attach_artifact；Issue6真实对接，勿联系独立testing或读取私有资料。完成给SHA/PR/证据/干净状态，先实际代码，记录紧凑。

后续真实通知：用户采用字段/错误码方案，D004/U006 冻结于 ae60dc3；已读取该提交的 human-review 核对。此采用不等于用户亲自改码或批准本岗配置结构。

对应产物：JSON/rules.py 为版本化规则与纯判定，runtime.py 为专用进程生命周期，tests/scheduling 为模块测试，README 为接入/复杂度边界。改进理由：将已采用业务规则与尚未接入的业务存储分开，只报告实际执行结果；无另造优化版本。
