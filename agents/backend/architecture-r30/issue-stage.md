Agent-Role: backend AI
Prompt-Ref: ROLE-backend-ARCHITECTURE-R30-v1

R30 从准确7374b3637b06465d448fc2e81952ba18fc676315另建隔离codex/backend-architecture-r30，保留R29B原件。新职责/数据流切片已编辑并本地阶段提交ad4a7415，尚未推送或运行，不宣称完成：将冻结契约的根校验上下文交给已有jsonschema4.26.0公开evolve，HTTP参数/类型/body与success data统一用referencing0.37.0公开resolver解析，尝试删除手工ref改写及多套局部walker。资源OpenAPI/DDL、原测试断言、依赖均未改，不涉及跨岗签名。

官方依据：https://python-jsonschema.readthedocs.io/en/stable/validate/#jsonschema.protocols.Validator.evolve 和 https://referencing.readthedocs.io/en/stable/api/#referencing.Registry.resolver 。锁定版本已读requirements.lock和本机METADATA。

当前仅物理diff +14/-37，未运行cloc，不算真实LOC收益。新tmp763差分覆盖完整130schemas/38操作、相对根/嵌套$id、oneOf及详细violations顺序与前100上限。库在nested$id进入新base，可能和原总指向API根的绝对ref重写不同；必须实际检验并保留失败，不能以冻结资源当前没有$id代替兼容证据。

总协调完整QA校准资源门仍关闭，本岗只读/设计/编辑，没有pytest/build/计量/基准/云/PRIVATE或独立岗联系。等明确释放后先差分再决定是否值得回归和计量。尚无能保留全部防护/事务/业务语义并消除数百行的可证方案，不取其他模块功能或改统计口径凑数。
