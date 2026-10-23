# 真实产品门禁

`.github/workflows/product.yml` 的状态名为 `static`、`contracts`、`coverage`、`frontend`。它们不会设置 `reviewer/stage` 或修改仓库保护；是否加入 main 必需状态由总协调操作。文档初始化不代表产品门禁已通过，首个产品合入前仍须四项真实运行和独立审核。

- static：官方Compose schema、Docker Compose配置、官方Nginx容器 `nginx -t`、部署/CI守卫单元测试、Ruff、生产Python Bandit。应用包/锁/测试/规格缺失会明确失败，即使部署配置检查通过也不会给产品绿灯。
- contracts：真实MySQL8.4和RabbitMQ services，显式迁移到一次性 `t44_ci` 库；分别跑 `contract`、`integration`、`fault` markers。每类必须有实际通过的用例，空集合、失败、全跳过或任一跳过均失败；模块自测不等于独立验收。
- coverage：真实MySQL/RabbitMQ与迁移，运行全量 `backend/tests`，采集整个 `backend/t44`；不配置omit、不排除未导入模块或 `pragma: no cover`，核对每个生产 `.py` 出现在报告。分支也采集，但只按 `covered_lines / num_statements >= 80%` 强制生产源码行覆盖率，不给分支/函数额外设80门槛。
- frontend：Node24、pnpm11.25.0，冻结安装、`typecheck`、生产build、真实 `test:coverage`。通过Vitest JSON拒绝零测试/跳过占位，coverage-final必须包含 `frontend/src` 的全部 `.ts`/`.vue`；仅无可执行内容的 `.d.ts` 声明文件公开排除。只强制行覆盖率80%，statement/function/branch完整报告；不能拿后端覆盖率或语言平均数替代。

前端责任岗应提供 `typecheck`、`build`、`test:coverage` scripts，并让coverage支持CLI的Vitest JSON及Istanbul json/json-summary输出；业务测试尚未存在时失败是预期现状，不能加 `--passWithNoTests` 或跳过门禁。后端提供带哈希 `requirements.lock`、pyproject markers、真实CLI和测试；目前这些实现尚未交付。

CI工具版本在 `requirements.in` 显式固定，传递依赖与哈希在 `requirements.lock`。Actions使用2026-10-23向官方API解析的固定commit；MySQL/RabbitMQ/构建基镜像固定官方多架构摘要。升级需重新解析官方来源、检查工具与runner兼容并提交差异，不能静默漂移。

原始stdout/stderr、JUnit、迁移与服务日志、静态JSON、逐文件覆盖率/HTML等上传为绑定 `${github.sha}` 的 artifact，保留14天。测试依赖的账号均是公开标明的一次性CI凭据，不用于运行环境。工作流只读仓库权限，不使用 `pull_request_target` 或共享生产秘密。

本地纯工具复现（不代表容器/应用验证）：

```sh
uv venv deployment/.venv --python 3.12
uv pip sync --python deployment/.venv/bin/python --require-hashes scripts/ci/requirements.lock
deployment/.venv/bin/python scripts/ci/validate_config.py
deployment/.venv/bin/python -m unittest discover -s deployment/tests -v
deployment/.venv/bin/python -m unittest discover -s scripts/ci/tests -v
deployment/.venv/bin/ruff check --config scripts/ci/ruff.toml deployment scripts/ci
T44_CI_REPORTS=agents/deployment/runtime-validation/ci deployment/.venv/bin/python scripts/ci/static.py
# 应用缺失时最后一步退出1；reports中的missing字段是阻塞证据，不是通过结论。
```

应用齐备后的本地 `run_tests.py contracts/coverage` 还须显式准备一次性真实服务和迁移；不能在生产库运行故障自测。开发机本轮无Docker，未执行完整工作流、容器构建或压测。独立验收由总协调另行隔离派发。
