# 库依据与边界

本机与requirements.lock准确jsonschema4.26.0、referencing0.37.0；未新增校验库、未调用新evolve路径。官方说明同一schema重复实例验证适合复用具体validator实例：[jsonschema4.26校验协议](https://python-jsonschema.readthedocs.io/en/v4.26.0/validate/)。原生iter_errors/descend源码检查见[锁定4.26.0实现](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py)。这里只据源码和8线程差分验证本候选，不宣称库有额外未明确的线程安全承诺。

缓存仅模块导入时从准确冻结SPEC已知对象编译，不改变原构造器/引用URI算法；调用方任意动态schema及root/nested$id保持原始路径。性能记录为本机ABBA CPU微基准，不能替HTTP P95、400并发600s或SUT结论。
