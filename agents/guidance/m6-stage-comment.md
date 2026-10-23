Agent-Role: guidance (AI author/operator; not student manual work)
Prompt-Ref: ROLE-guidance-M6-v1

M6已在独立worktree/codex/guidance-m6编写中文“怎样读懂和检查本项目”及5项待学生本人完成练习，来源固定0783a42b26038d7d3e5a1fe07ae8219a47f06493。主稿docs/guidance/M6-learner-guide.md，逐字AI询答M6-actual-qa.md，45文件hash/40函数位置M6-source-manifest.json；阶段提交push后可在该分支查阅，精确SHA另由Git回执交总协调。

按真实源码说明Vue表单→契约生成的38操作→FastAPI endpoint.handle→Runtime.execute→Business/Tasks.changeTaskPlan→Call.cas/schedule_diff→SQL事务/audit/outbox/幂等快照；消息网络在DB事务外，scanner是另一入口共用Runtime。后端AI纠正了本岗询问中的execute_operation/save_task泛称，不冒记学生发现幻觉；前端AI解释本地检查不等于业务守卫。两次真实问答均逐字保留，不称人类访谈。

R001只作为本人观点依据；R002仅读公开provenance，未读其私密原文/封面/任何tmp/independent内容或未发布测试，未联系独立测试。无学生新答卷/亲改/断点/亲测证据，不写最终学生研究正文。

最近完整绿色仍仅8323692：437BE/65FE与准确Docker合成演练。root刚报0549 BE+c79 FE合入42243eb23aedf0edda7541ad83fd87ec3d17b616并触发CI，本岗不等待、不预判其结果；6186+pending仍超5100，原正式P95三组失败、v2整体未完、v3先冻结0执行均保留。

本轮只有只读源码、文稿/JSON及链接/hash/diff核对；没有运行产品、测试、负载、浏览器或渲染，不设置审核success、不合并。
