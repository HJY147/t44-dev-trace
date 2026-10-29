# R30契约上下文实际候选：拒绝集成

- 操作者：固定后端AI；Prompt ROLE-backend-ARCHITECTURE-R30-v1；起点`7374b3637b06465d448fc2e81952ba18fc676315`；候选`ad4a7415f195fff571b67e7d4b7b5cada5c28f72`。
- 实际结构：contracts用jsonschema公开evolve持有根上下文，引用解析委托referencing公开resolver，API参数/类型/body及成功data共用入口；仅改两个产品文件，无新依赖/冻结资源变化。
- 官方依据：[evolve](https://python-jsonschema.readthedocs.io/en/stable/validate/#jsonschema.protocols.Validator.evolve)、[Registry.resolver](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry.resolver)。本机METADATA与锁均jsonschema4.26.0、referencing0.37.0。
- 资源门关闭时只读/设计/编辑及本地阶段commit。root明确释放后才跑以下全部检查；实际释放提示已原文补入prompt。
- 新差分174项：**173通过、1失败**，0.72秒。准确基线接受嵌套`$id`内的本地TaskState ref及`{"state":1}`；候选抛`_WrappedReferencingError`。原始失败log/XML/命令保留，不改断言或豁免失败。
- 其余差分含全部130schema、38操作元数据、参数/oneOf、根$id、完整错误路径/顺序及前100上限一致。冻结OpenAPI当前无$id，不足以代替通用validator行为保持。
- 原986/856 SQLite HTTP **134通过**，32.26秒、0失败/错误/跳过；1条原上游Starlette弃用警告。冻结业务回归通过**不能抵消**新增通用引用回归。
- 原固定script/cloc2.10准确提交实测：**5880→5861，候选净减19**；仍超761，两次require-range均退出1。物理diff的23没有当作cloc。
- 修复成本判断：保持旧任意嵌套$id→API根语义，直接方式是保留原绝对ref规范化；恢复原validator/规范化后只剩约7行静态预算。另造自定义ref keyword扩展还需处理嵌套$schema演进，复杂度与风险不配十余行收益。该预算不是已实现收益。
- 决定：**拒绝evolve这条已实现结构方向，不建议集成**。保留原可运行候选、真实红和完整计量；接下来将两个产品文件恢复准确基线，最终应用净减应为0，需以实际后续记录为准。
- 尚无保留全部防护、错误次序、权限、事务/幂等/审计/CAS/锁仍省数百行的可证方案。Runtime、可信行防护和各业务门禁有独立语义；不为规模删除或迁入excluded文件，也不把这个负结果说成数学上证明不存在其他架构。
- 没有改原测试/断言/统计口径或既有岗位边界，未读PRIVATE/未公开独立资料，未联系独立测试岗，无云/完整CI/真实MySQL/MQ/正式性能新结论。
- GitHub阶段记录：https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6490016627 。没有merge。
- 原始证据：differential-initial.log/xml、original-http.log/xml、两command.json、count-before/candidate.json/log、count-commands.json、static-initial.json、phase1.json。
