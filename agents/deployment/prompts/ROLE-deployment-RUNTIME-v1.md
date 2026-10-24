# ROLE-deployment-RUNTIME-v1 实际岗位派工

来源：总协调发给deployment的实际消息。以下是岗位提示词原文，不冒称用户原始提示词；与BOOTSTRAP/M0是不同阶段，不凑作同一提示词演进。

> ROLE-deployment-RUNTIME-v1：开始真实部署/CI工程实现，不再只写初始化资料。用户已授权开发、阶段commit、公开GitHub。必须在独立 worktree `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment`，分支codex/deployment-runtime（已ff到4b3d6e5）。先读该树AGENTS/本岗TASK/requirements/architecture/业务v1，旧初始化“不可写代码/不可GitHub”被本轮覆盖。你只拥有 deployment/**、compose.yaml、.github/workflows/**、scripts/ci/**、本岗agents/reports/modules/handoff及本轮prompt归档。Dockerfiles全放deployment避免改前后端目录。其他岗正写契约/DDL，可只读根目录 drafts 或直接问backend（t44.api:app同步FastAPI，persistence、messaging、scheduling同包独立进程；backend/pyproject.toml+requirements.lock；PYTHONPATH=backend）。Frontend Vue3+TS+ElementPlus，Node24、pnpm11.25.0；构建后静态反代/api/v1。搭建 Docker Compose 单机 MySQL8.4、RabbitMQ、4workerAPI、消息消费者、调度、反代+前端；数据/队列持久卷、健康启动/迁移独立步骤、密钥随机生成脚本及.env.example（仅占位），默认端口仅loopback/SSH隧道，正式TLS说明，不暴露DB/MQ公网。账号初始化与token撤销由backend CLI，部署提供封装不造用户管理API。备份恢复脚本需校验目标、显式选库，不能执行破坏性操作。
> 实现真实 GitHub Actions static/contracts/coverage 三项门禁+frontend build，MySQL与RabbitMQ真实services供模块集成/契约/故障自测；应用测试尚未存在就让步骤明确失败，绝不造成功/skip空测试。与backend协调pytest markers与入口，覆盖全部生产Python t44包>=80；CI输出原始报告。Docs-only提交可单独清晰scope，但首个产品合入前必须真实三门禁。当前根没有Docker，不能宣称compose已构建；可以安装/使用安全纯工具做配置静态验证，适当浏览官方主文档核对镜像/actions版本。不得租服务器/付费/买域名，不联系独立测试。所有跨岗需求通过Issue #7及对应Issue实际评论，保留正文body-file。日志+模块报告+handoff+本轮实际prompt必须更新。只在本worktree显式add本岗文件、commit（footer角色/PromptRef/Refs #7），可push本岗分支并创建草稿PR，创建成功必须调用attach_artifact；不合入main，不发审核成功。先给我接口/路径假设，继续做到本轮可完成的真实配置与验证。

## 实际后续澄清原文

> 补充实测本机工具路径：Node `/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node` v24.19.0；pnpm CLI `/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.cjs` 11.25.0，可绝对node调用。uv `/Users/yang/Library/Application Support/MinerU/tools/uv`；Python3.12.10 `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3`；根`.venv`已创建（仅规范校验工具）。确实无Docker。请别加公开未鉴权health业务API；契约要求统一鉴权，健康可命令检查进程/数据库或服务鉴权，与backend确认。统一入口建议 `python -m t44.cli ...` 迁移/账号/撤销，messaging与scheduling的 __main__由责任岗实现。CI使用现有真实markers/路径前请问backend，空实现阶段失败属正常不包装成功。

> 创建草稿PR时 base 用 `codex/team-bootstrap`（暂不直接main），仅展示本岗新增；主干仍由#13后续整合，后面可调整。CI状态名按你真实job名static/contracts/coverage/frontend提供，我在存在真实运行后再把它们加进main必需门禁；当前只有reviewer/stage。pipeline依赖尚缺时红灯正确保留，不算产品测试已执行。不要自行改保护/合并或承诺400并发达标。GitHub Actions已实测enabled=true，PUBLIC MIT元数据也再次确认。

> 契约有一个真实集成约束请处理：body上限1MiB，413必须返回冻结JSON错误形状，不能让Nginx默认HTML替代（specs/contracts/README已有明确要求）。可把反代上限略高，让1MiB由API校验/脱敏审计；更大请求也需Nginx统一JSON映射，audit_id=null如无DB记录，别假称已审计。访问日志不要记录Authorization/口令/body/原始querystring，按request_id+status+耗时等最小字段。无需新增鉴权探针。

> 补充避免擅增作业门槛：覆盖率>=80当前冻结为每语言生产源码“行覆盖率”>=80（前端statements可一并显示），函数/分支覆盖率完整报告但不额外强制四项都80，原任务书未指定四项。关键失败/并发分支仍必须有真实用例。不要排除未测组件/模块来提高分母；声明/生成物排除公开。请CI脚本明确line阈值，别把额外四阈值当用户/教师要求。

## 产物映射

Compose/Docker/Nginx、ops.py和恢复文档落实运行边界；scripts/ci与workflow落实真实门禁及缺实现失败；本岗日志、交接、Issue正文与验证证据落实留痕。实际操作者为部署岗位AI，未记作用户亲自改码或独立验收。
