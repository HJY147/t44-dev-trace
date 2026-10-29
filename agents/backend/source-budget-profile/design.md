# 870离线C原型：先行设计，生产不准入

作者后端AI。隔离树backend-source-budget-profile，分支codex/backend-source-budget-profile，基点cee7a574fb2061c76123070e304655b6c12db967；应用字节与bc5aef9c62393134582affb7a690acb33ac2b833一致。先提交本设计/实际prompt，之后才写870工具；本设计时工具与基准尚未运行。禁止改backend/t44、锁、14冻结、统计口径或应用B/C。

## 原路径与原型

锁与本机实际包均jsonschema4.26.0/referencing0.37.0。原contracts.validator(schema)每次递归_absolute_refs→加urn:t44:validation→新FormatChecker→新Draft202012Validator；violations完整list(iter_errors)后仅输出前100个(path,rule,message)，message为固定规则名，不含输入原文。

候选只在工具内复现既有未应用C：用带$id=urn:t44:api的SPEC浅根副本、同公开Registry/FormatChecker构造根validator，调用公开root.evolve(schema=...)，每次保留独立validator/generator，不在根执行iter_errors，不缓存payload/结果，不改原SPEC/registry/checkers。仍非共享validator线程安全证明。[官方4.26协议](https://python-jsonschema.readthedocs.io/en/v4.26.0/validate/#jsonschema.protocols.Validator.evolve)说明派生实例继承未覆盖的属性与引用行为；[referencing0.37说明](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry)说明Registry不可变。仅这些API语义不能替代本项目等价性/线程/HTTP验证。

代码身份预先固定：contracts/__init__.py SHA ee2a72d0ee435a63686e80548da2fdc1b0b2df05c399820e19973f8100dc8cdc；运行副本openapi.json SHA a77a5cd635b8f6a9927b60f9befac017055442504e34a95b40eddda809e2782f。870校验实际import __file__/上述hash与锁版本，记录sourcebc5/tool commit；无git/网络/数据库子进程在诊断内运行，不读任何凭据/独立资料。

## 一次有界batch与输出

870仅标准库顶层定义+opt-in main；pytest/import不导入t44、不跑基准。需要--run、全新输出文件、精确tool/source/hash；生产import限t44.contracts，无api/services/DB。单个main从导入前启用墙时15秒、CPU软12/硬15秒限额；异常/超限保留部分JSON与非零退出，不重跑刷数。先语义比较，失败即存原件停止计时扩展。

19个自有合成Schema/JSON样本：Plan合法/额外字段/非法日历/1000及9999年/布尔小时；Id布尔非法和1.0合法；EvidenceRefs合法/布尔kind非法；TaskCreate合法/嵌套非法；TransitionRequest合法start/非法action；ContractValidationRequest合法category1/非法payload；程序生成外壳嵌套ref；105布尔Id数组（完整错误与前100截断）；不存在的本地ref应双侧抛引用异常failclosed，不能被当valid。无未知http远程schema。

比较双侧完整错误数、保持原顺序的前100(path,rule,message)；无效引用记录异常类型、双侧failclosed。记录独立实例和交错generator不污染、SPEC/checker集合前后不变；不做线程测试/不声称全38操作等价。样本合法性有固定预期，不能因两边都错就记通过。

固定30轮用于构造；iter_errors另为每轮/每case预建独立validator后测完整列表，预建成本另记而不混成纯iter时间；原型根一次初始化单列成本。CPU+墙时分开，构造占比只指这些合成构造/迭代两部分，不指HTTP耗时。cProfile每模式5轮完整“构造+list+前100映射”调用，函数路径归一到项目/stdlib/site-packages相对路径，exclusive/inclusive分开，不把inclusive求和。原始JSON含案例输入/错误签名/测量/热点和实际源hash，都是自有合成数据。

成功也只形成离线候选建议；不能解释独立正式P95、SQL排队/线程池/网络或全HTTP，不能推导生产线程安全/性能达标。只执行一次；任何真实失败/不等价原件保留，根收到后才可能另准入设计/实现。
