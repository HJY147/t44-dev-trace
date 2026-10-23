Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-HANDOFF-v1

答复backend基础编码阶段的报告插件问题：部署CI当前实际命令是标准pytest JUnit，不要求pytest-json-report或pytest-cov。

```sh
python -m pytest -c backend/pyproject.toml backend/tests --strict-markers -m contract --junitxml=reports/ci/contracts/contract.xml -ra
# integration/fault 各自同样运行；全量测试不加-m：
python -m coverage run --rcfile=scripts/ci/coverage.ini -m pytest -c backend/pyproject.toml backend/tests --strict-markers --junitxml=reports/ci/coverage/junit.xml -ra
python -m coverage json --rcfile=scripts/ci/coverage.ini
```

`backend/tests`递归包含 `backend/tests/backend`。工具锁为pytest9.1.1、coverage7.17.0；模块可以为自己的JSON命令验证额外插件，但不是本CI前提。markers为contract/integration/fault，各自无真实用例或跳过占位会失败。纯domain基础还不是API/真实服务集成阶段，不能给基础测试改marker或写stub来满足门禁；缺实现红灯保留。只强制完整生产t44源码行覆盖率80%，分支完整报告不另设80门槛。
