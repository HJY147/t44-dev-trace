# 实现目录与进程约定

状态：实现派工约定，不代表目录已实现或接口已冻结。初始化任务中的阶段限制由新的明确派工覆盖，未授权的共享修改仍禁止。

| 责任岗 | 可写产品路径 | 稳定边界 |
| --- | --- | --- |
| backend | backend/t44/api.py、cli.py、settings.py、domain/、services/、contracts/、resources/review-template.json，backend/pyproject.toml、requirements.lock，backend/tests/backend/ | `t44.api:app`；鉴权、统一错误、业务状态门面与组合根；数据库连接由注入门面提供 |
| database | backend/t44/persistence/、backend/migrations/、backend/tests/persistence/ | 模型、UoW、参数化仓储、锁与持久化能力；迁移/合成数据命令由统一CLI适配 |
| messaging | backend/t44/messaging/、backend/tests/messaging/ | `python -m t44.messaging`；发布确认、消费确认、通知门面、降级与恢复 |
| scheduler | backend/t44/scheduling/、backend/t44/resources/escalation-rules.json、backend/tests/scheduling/ | `python -m t44.scheduling`；版本化规则解释、APScheduler、持久扫描与升级门面 |
| frontend | frontend/ | Vue 3、TypeScript、Element Plus；只调用冻结API，不自行决定状态/权限/超期升级 |
| deployment | deployment/、compose.yaml、.github/workflows/、scripts/ci/ | Dockerfiles、反代、环境与运行脚本、真实CI；不改业务实现或测试断言 |

生产Python包统一 `backend/t44`，`PYTHONPATH=backend`。Python 3.12、同步FastAPI+SQLAlchemy2/PyMySQL、Pika、APScheduler；Node 24与pnpm 11.25.0。数据库使用MySQL 8.4，消息使用RabbitMQ。依赖锁由后端维护；其他岗先提出依赖需求，避免并行修改锁文件。

独立测试的验收目录及私有用例按隔离协议另行交付，不属于开发测试目录。模块自测只是责任岗验证，不得称独立验收。

CLI命令、环境变量和门面签名须由责任岗在契约/持久化文档中确认。部署探针用进程、监听与数据库直探或服务身份，不额外开放未鉴权业务API。组件实例在组合根创建并注入；API多worker不各启动一份调度器。

各自worktree、codex/分支和显式路径提交；总协调负责集成分支与公开PR。在规格冻结前可写独立配置和设计，未冻结接口不得进入模块联调。跨岗路径变更先在Issue提出并由责任岗修改。
