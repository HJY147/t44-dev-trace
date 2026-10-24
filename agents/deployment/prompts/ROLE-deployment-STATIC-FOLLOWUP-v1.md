# ROLE-deployment-STATIC-FOLLOWUP-v1

本岗为实际派工建立归档ID。

## 实际总协调派工原文

紧急但小范围静态修复，文档岗已释放槽。当前root dde39aa1c3ccf122caff5c24584ab69537d09007 已push（应用bc5不变），BE独立1行SQL候选74aeb2a PR42 product40047094732 的static原红已发现基底已有两处：UP022 tmp/deployment/864_native_serve_driver.py:58 run stdout/stderr=PIPE；B007 tmp/deployment/871_native_application.py:436 unused枚举index（它是unit tests，不是controller）。请独立codex/deployment-static-followup worktree从root准确基点，先设计提交，再仅这两处等价窄样式修复：capture_output=True；unused循环变量改_index等，不更改断言/案例/行为。不运行或import864实际driver（顶层会启动服务），不改deployment/native/application.py或runtime.py/活跃私密4h copies，root/native/controller084618/live92files均须保持，不能停止/重跑服务。保存2旧文件hash及对应真实Git前像、修改后hash与精确AST/stdlib意义核对，当前新源不能冒称原已执行归档字节/旧运行；原副本Git历史和CI红保留。仅Ruff必要2文件（现有CI同配置）与必要compile/现有871纯mock相关目标（若需要，不重复所有套），无新test文件/独立私密/信号/HTTP/SQL。请约5分钟给最小可接线实现SHA，再完成prompt/log/module/handoff/Issue7实际COMMENT全文GET和最终封档，准确SHA让BE合入其candidate新提交触发新CI，不重跑旧红run。你可与BE通过Issue对接。避免额外修改范围，测试脚本改名/移目录/新增豁免均不要做。
