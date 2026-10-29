# 测试文件

按用户要求，测试脚本统一放在本目录，编号按创建先后递减：`999_xxx`、`998_xxx`，依此类推。现有脚本依 Git 首次加入的时间排序，同批时间相同时按原路径排序；原路径、提交和新文件名见 [迁移清单](../records/validation/test-file-layout.json)。后续新增文件先领取清单中的下一个编号，避免各岗并行重号。编号只用于排序，不表达测试重要性。

- `backend/`：Python 模块、契约、集成与故障用例。运行 `python -m pytest -c backend/pyproject.toml tmp/backend`。
- `frontend/`：Vue/TypeScript 用例及浏览器检查。运行 `pnpm --dir frontend test`。脚本会创建被 Git 忽略的 `tmp/node_modules` 依赖链接。
- `ci/`、`deployment/`：门禁及运维检查，与产品测试结果分开统计。
- `validation/`、`documentation/`：设计和文档的校验脚本，不纳入产品测试覆盖率。

`conftest.py` 是 pytest 固定名称的夹具配置，`__init__.py` 是包配置；两者不包含测试用例并保留框架所需文件名。历史日志保留执行当时的命令和路径，不为迁移重写证据。独立验收私有用例不得由开发岗读取，后续单独隔离在本目录的忽略子目录。
