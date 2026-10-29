# R30 契约上下文垂直切片（尚未运行）

- 起点：7374b3637b06465d448fc2e81952ba18fc676315；操作者：固定后端 AI。
- 结构依据：原contracts逐调用递归改写本地ref；API另有参数、类型、body三处手工解引用，成功data又直接拆ref。它们属于同一份冻结契约的解析职责。
- 已编辑：contracts根Draft202012Validator保留完整schema上下文并公开evolve；共用Registry.resolver.lookup实现resolve；API和成功data统一取该入口。没有资源OpenAPI/DDL/依赖变动。
- 正式API依据：[jsonschema evolve](https://python-jsonschema.readthedocs.io/en/stable/validate/#jsonschema.protocols.Validator.evolve)、[referencing Registry.resolver](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry.resolver)。已读本机锁定源码；METADATA与requirements.lock均为jsonschema4.26.0、referencing0.37.0。
- 当前源码diff为+14/-37物理行，不等于cloc。还没运行导入、pytest、build、计量或基准，保留root资源隔离门。
- 核心风险：evolve保留父resolver；进入嵌套$id时库会切换base，而原绝对ref重写总指向API根。冻结两份OpenAPI未发现$id（rg退出1为无匹配），仍须跑合成$id差分，不能只以当前资源不含$id宣称完整兼容。
- 新tmp763差分保留实际基线模块，比较全部130schemas、38操作元数据、参数/分支、根/嵌套$id、oneOf和120条错误的前100顺序；旧HTTP测试仍原样运行。没有已知旧测试需要迁移，不读未发布独立资料。
- 相邻大头：Runtime的事务/幂等/审计，domain可信行防护、各操作业务门禁均有独立语义。尚无保留这些语义仍可省数百行的可证方案，不重复旧OperationPlan净增路线。
- 释放后顺序：先新差分；保留失败原件并决定是否修复/拒绝，再原HTTP回归；阶段commit后固定原counter/cloc计量。若兼容或净值不成立，不建议集成。
