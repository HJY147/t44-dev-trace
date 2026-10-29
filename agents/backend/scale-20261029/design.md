# 2026-10-29 契约构建复用：先测量的后端候选

操作者为后端 AI 岗，基线 `f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`；实际派工见 prompt.md。本设计先于产品改动。固定应用规模 5898 行、超限 798 行，仍不达标。本候选主要验证性能，允许如实记录净增代码。

## 约束及候选

仅修改 backend/t44/contracts/__init__.py。所有请求校验、提交前 data 校验和每次 HTTP 完整 envelope 校验继续执行；不改变成功/失败 schema、前100项输出、全部错误遍历、路径/规则/顺序、格式校验、鉴权、事务及幂等。公开 validator(schema) 仍返回新的、可独立修改的实例。

violations 内部尝试复用最多128项的私有编译实例。键由完整 schema 的有类型、有插入顺序的结构快照，以及 FormatChecker 类级注册项快照组成。dict/list 递归拷贝，数字/布尔类型分别标记；非原生 Python JSON 类型或不可哈希注册项回退原 validator 路径。输入 schema 修改后生成不同键；公开实例/schema/checker 修改不得污染后续 violations。缓存不保存 value 或错误；每次运行 iter_errors，完整列举后才截取100。schema 来自服务端契约，非用户请求体；128是项数上限，不宣称任意外部超大 schema 的字节上限。

禁止把根对象内容排序来拼键，因为错误顺序受关键字顺序影响；禁止用 schema id 单独做键。FormatChecker 类级新增/替换/移除会生成不同键；运行中并发修改其全局注册表不属于受支持服务操作，既有实现同样无注册锁。引用 SPEC 保持原 Registry/Resource，不能用另一份冻结副本吞掉运行期引用内容改变。

## 依据与风险

准确依赖 jsonschema4.26.0 / referencing0.37.0 / attrs26.1.0。检查对应源码：Validator.iter_errors/descend 使用本次局部变量，modern Resolver/Registry 返回新的解析状态；不访问会引入旧可变 RefResolver 的 deprecated .resolver 属性。共享实例仅限私有缓存，格式 checker 为构建时快照。仍须线程/交错 generator 和动态 schema/SPEC/格式器的行为差分验证，不能以源码推断代替测试。

官方来源：[jsonschema4.26.0 Validator](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py)、[FormatChecker](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/_format.py)、[referencing Registry](https://referencing.readthedocs.io/en/stable/api/)。这是基于该版本源码的适用性判断，不是上游发布的通用线程安全承诺。

历史870诊断构造仅占混合样本约3.7%，因此本轮不预言显著端到端收益。若真实微基准不稳定或变慢，保存候选和失败，建议不部署、不花钱重测。

## 本轮验证计划

1. 新774测试直接以基线 Git blob 动态加载作差分 oracle，不抄写原实现。覆盖原870有限样本及新增关键字/属性顺序、105错误截断、异常、schema mutation、公开对象修改隔离、格式注册动态变化、引用内容变化、交错 generator/多线程和缓存上限。
2. 旧986 HTTP原字节保留，实际 TestClient/SQLite 契约回归；必要补充两层校验确实继续运行的HTTP探针。OpenAPI两副本与冻结文件hash不变。
3. 先启动纯CPU、有界ABBA重复微基准，分别报告微小/嵌套/错误输入和实际单个操作样本，不推算400并发或云P95。
4. 准确提交后原固定脚本/cloc2.10计数；不改计数边界。根协调集成后才运行全CI/云/独立验收。
