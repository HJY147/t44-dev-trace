# 818 通用故障归属

归属：**冻结工具程序错误**。没有证据将本次TypeError归为新env的project/iteration/ID元素类型问题，也不归为SUT业务缺陷。

冻结组件 `private/schema.py` 的 `validate()`（定义第7行）在第32行使用 `checks[t]`；此时`t`来自Schema的`type`，可为合法列表，列表不能作为Python字典键。

最小离线shape：instance为`0`，schema为`{"type":["integer","null"]}`。直接调用原冻结校验器得到`TypeError: unhashable type: 'list'`。对本次捕获响应做本地校验也在同一函数、同一行得到相同异常。两次复现均不发送网络请求，且该最小复现不依赖环境里的项目/迭代/任务ID。

组件SHA-256：`2d12831838fa622ffc4a5a5034c882cbae60561de088139f6ff97a208d1a634e`。八核心冻结承诺：`90f88ddc500a03e15f50ea2672ca730e1ea277813920e104c90f4d8829a9b24d`。

原D01 PASS、P01 FAIL、正式性能NOT_PROVEN均保留。未修改八核心、case/oracle/阈值，未额外请求SUT、未重跑或延长时间。完整捕获响应是否满足其全部Schema没有因此判为通过；原加密证据与keys仍仅私有保存。
