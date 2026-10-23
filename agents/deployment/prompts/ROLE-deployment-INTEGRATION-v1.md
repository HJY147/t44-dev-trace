# ROLE-deployment-INTEGRATION-v1 实际岗位派工

来源：总协调实际消息，不冒称用户原始提示词或人工改码记录。

> 恢复完整部署联调 ROLE-deployment-INTEGRATION-v1。请自己worktree merge codex/integration当前完整应用基点（含BE ba1018+DB9aeb+FEbd13414+MQ9481+sched a8b491），不要碰root索引。已具备完整38API/真实CLI、seed、独立MQ/sched。
> 优先修真实静态Docker构建路径bug：frontend/src/contract.ts import '../../specs/contracts/openapi.json'；旧web Dockerfile WORKDIR /build COPY frontend ./ 未提供/specs。保持/build/frontend工作目录、COPY权威specs/contracts到/build/specs/contracts，调整Dockerignore与最终dist路径，必须实际Docker build验证（本机无Docker，可GHA runner）。读取真实scheduler/__main__.py与Issue7调度交接6361329227，补service-token JSON0600只读挂载/共同flock持久路径及初始化/续期操作；服务凭据无公开输出。既有BE CLI service-token已实现，不再假设缺失。
> 按实际应用做容器build+Compose up、显式项目库迁移/init-user/seed、API多worker/独立consumer+scanner/HTTP+前端静态路由真smoke；用GHA托管Linux，不购买云资源或声称已经云部署。必要备份+隔离库恢复真演练，不能只写脚本就称成功。统一CI仍需static/contracts/coverage/frontend真实绿，whole t44>=80/全srcFE>=80保留严格条件。当前root即将push integration发统一原CI以确认新故障；你新增Docker应用集成job独立真实运行/日志归档。修完先checkpoint SHA供root合并，别等所有报告。每岗本职代码+日志/报告/handoff/prompt/自己commit push/PR15更新COMMENT，对独立测试无通信/不读其私有资料。

## 实际后续文件规范

> 用户新明确：test文件统一项目tmp/，最早999_xxx、最新998_xxx递减编号。root会按首次引入Git时间+路径稳定顺序，机械迁移已提交backend/tests/frontend/tests/scripts/ci/tests/deployment/tests所有测试脚本，发布映射+SHA；conftest.py fixtures无测试用例保留框架必需名。你先别改现有测试路径/发现，生产Docker/compose可继续，待迁移SHA后由你更新CI preflight/run_tests/static/checkFE路径与实际Docker job。root更新backend pyproject pytest模式和FE Vitest配置/相对import，让迁移可执行；计数脚本识别tmp为tests，不改生产口径。新增测试先在tmp/并向root要递减号，避免并行撞号。

产物对应：web构建目录/权威契约资源修复，私密服务凭据与共享锁，真实Linux Docker联调/备份恢复job，实际证据及交接。模型/操作者仍为部署岗位AI，不把模块自测写成独立验收。
