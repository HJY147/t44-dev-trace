# 818 冻结工具兼容性缺陷事实

本次performance原始P01状态FAIL，异常为 `TypeError: unhashable type: 'list'`，发生在负载cohort之前的HTTP200响应Schema校验。

本地只读复现：对捕获响应调用原冻结校验器得到同一异常；最小复现为 Schema `{"type":["integer","null"]}` 与值 `0`，仍得到同一异常。冻结契约声明了此种type列表，但冻结校验器的type分派不能处理列表。

此事实不包含私有业务payload，不改变用例/oracle/阈值，也不将该异常归为SUT业务缺陷。八个核心文件保持原哈希；本次未修改工具、未重跑。正式性能结论NOT_PROVEN。
