# 870一次离线诊断结果与N07建议

执行者：后端AI。设计先84fee744，工具提交964f4bb4796c6bcfa546f3ccba157ce2c5b88515后只执行一次；应用bc5字节不变。raw.json SHA91fad27a367f546f2e38d294f9ec4372bf3b6b23ab673955c5f966df39eacb0d，工具/实际import/版本/Spec SHA均核对Git对象。exit0，main总墙0.350673秒、CPU0.350167秒，15秒墙时/软12硬15CPU上限未触发。没有HTTP、SQL、服务、浏览器、凭据或独立资料输入。

## 观察范围

19个冻结Schema/自有JSON样本：双侧完整错误数及原顺序前100(path,rule,message)相同，且符合预先合法/非法预期。未知本地引用双侧同引用异常failclosed；105布尔Id数组完整105错误、公开映射只截前100，未以少检查换收益。每模式计时iter阶段570个独立validator/job，3450错误、30引用异常；源码、SPEC、输入及checker名字集合未变。

独立validator与交错generator通过。原工厂每实例独立FormatChecker，原型派生实例共享根的只读FormatChecker；这只是顺序诊断，不证明多线程安全。也未覆盖38个操作全部HTTP输入/响应、错误优先分类、跨draft/$id/anchor/dynamicRef。有限样本相同不能写成全等价。

## 分段原始CPU累计（各570调用；毫秒）

| 模式 | 构造 | iter_errors完整遍历 | iter前预建成本（未混入遍历） |
|---|---:|---:|---:|
| 生产工厂 | 3.670 | 95.267 | 3.895 |
| C原型 | 0.438 | 87.347 | 0.492 |

这里构造只占生产“构造+完整遍历”两部分的3.7094%，**在本合成混合里不占主要比例**。不是HTTP整体占比，且其中105错误数组显著加权遍历。C构造累计少3.232毫秒是本次观察；iter差异不作因果/统计收益结论：单次固定模式顺序、无重复置信区间，原型根一次初始化另列于raw.json。不能外推合法真实请求或270ms正式P95。

每模式额外5轮/95调用的cProfile使用默认elapsed计时，生产inclusive前列为signature49.121ms、iter_errors46.696ms、descend43.587ms、ref42.532ms；原型分别41.723/40.977/38.688/36.796ms。父子inclusive重叠不能相加或称独占CPU；所有相对文件/函数/调用数及exclusive/inclusive原值在raw.json。它只描述本批合成遍历，不诊断数据库/连接池/线程排队。

## 后续推荐

不建议把C作为解决当前正式P95或N07缺1207行的主要路线。生产未改，B/C都未准入；N07一页建议见n07-source-budget-one-page.md：仅旧C草案静态-10有可核预算且尚未实施，即便未来全证明也只到6297、仍超1197；扫描run14字段/通知分页重叠尚无可信净省，计0。没有可信1207删除方案，不削弱功能/守卫/类型/审计，不移计量根/转不计JSON。

若根以后认为10行语义简化值得成本，应另审根解析/未来draft与FormatChecker边界，补全38操作实际请求/响应/故障错误映射、实例/并发证明后才考虑生产；本轮不自动进入该阶段。重大架构/课程范围留人回来决定。

API依据仅官方主来源：[jsonschema4.26 evolve协议](https://python-jsonschema.readthedocs.io/en/v4.26.0/validate/#jsonschema.protocols.Validator.evolve)、[referencing0.37 Registry](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry)。公开协议允许派生继承属性/解析上下文，也可能切换validator类；Registry不可变不等于整套validator线程安全承诺。原Ruff工具F401/B023/F821初稿错误原log保留，静态修正后才唯一执行，没有调样本/次数刷数。
