新增项目内有限原生应用生命周期工具，并将限时命令的超时事实写入失败回执。当前修复实现为 `b23897879142de3bd77190c67d4947eccf1c8263`，application.py SHA256 `5ed6844d4b44dcb9561141f9984100fcb034ad6f0984b4a4863219694c5dfe98`；先行设计为 `7f4845e`。

已发表 P2 `NATIVE-CAPTURE-TIMEOUT-01` 的原审核 [COMMENT5634837225](https://github.com/HJY147/t44-dev-trace/pull/34#pullrequestreview-5634837225) 与精确5ef/0a6原红完整保留。capture现在首次超时即记录timed_out=true/success=false，即使SIGTERM后actual child rc0仍抛OWNED_COMMAND_TIMEOUT；普通非零保持OWNED_COMMAND_FAILED。清理仍超时也写stop_unconfirmed和实际返回码（未退出为null）及部分输出摘要，再抛COMMAND_STOP_UNCONFIRMED。拥有权/信号权限不变，产品代码仅capture AST改变，runtime.py及旧ApplicationGuards类均未变。

同一公开原断言在旧代码真实红→修后绿；只执行现有871的五项CaptureGuards：正常0、普通7、超时后0、超时后-15、清理未确认/null，均通过，并保留actual child code。Popen/身份/等待/SIGTERM全mock，未启动真实被测进程/服务、读取私密输入或重跑cycle/其他守卫/中性套件；Ruff和diff通过，初始ClassVar诊断原件保留。新证据入口 `agents/deployment/native-capture-timeout-validation/README.md`，精确源/AST和实际五项receipt见scope-and-source.json、capture-final-five-boundaries.json。本P2等待根专项复审，自检不代表审核放行。

历史实际演示仍绑定 `0a6da88c404c04515c3c07039f0e231908fddc0e` / SUT `bc5aef9c62393134582affb7a690acb33ac2b833`，其原run2 driver0/cycletrue/cleanuptrue保持；新修复代码未获完整cycle验证。历史API4workers/consumer/UI HTTP代理、60.303070秒扫描、TTL300凭据轮换/回收与全部自有进程退出见 `agents/deployment/native-application-validation/README.md`。原run1 exit1/cleanupfalse不改，16confirmed事件/26通知发生于run1，run2仅既有ID复核，不称再次publish。

只使用根明确的新demo库与私密CRUD账号，不改业务/锁/规则/契约，不含迁移/reset/reseed/DDL。现保持停机；未做完整浏览器业务、独立验收、性能、云或生产安全批准。本PR保持草稿，不合main。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-NATIVE-CAPTURE-TIMEOUT-v1
Refs #7
