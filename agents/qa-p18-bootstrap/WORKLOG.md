# 独立初始化工具审核岗

职责：只审中性0b941a6d两文件与冻结bcec产品API规则，不修改被测源码。独立清单先于实现阅读冻结于68ac742b。未阅读开发日志、报告、提示词、作者测试，未联系其他工作岗。任务提示词标识：parent-neutral-P18-bootstrap-20261031；按中性需求直接制定独立用例，无改写成用户原话。

依赖导入fastapi/starlette/httpx/pytest成功。产品bcec backend/t44及specs/contracts与本worktree相同，git archive核对后git status无产品变动。SHA逐字匹配。

命令：
PYTHONPATH=backend /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend/.venv/bin/python -m unittest discover -s agents/qa-p18-bootstrap -p 'test_*.py' -v

结果：18 tests / OK；5个真实产品本地API路径，其余工具合成/本地文件/注入传输测试。没有外部网络请求、Docker或作者测试调用。合成库测试中的SQL仅创建合成数据及合成负例，不是修复生产状态。首批8项、补充16项和最终18项均通过，保留最终独立测试源码供复跑。

局限详见PUBLIC报告；MySQL/现场身份、真实TLS及660s轮未验，外层入口集成由其他独立任务负责。
