# C的源码预算：已核事实与最小删重设计（未实施）

作者/静态操作者：后端AI。准确应用C=`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`。现有cloc2.10原件确认 **后端5211 + 前端1099 = 6310，66文件，上限5100，超1210（约19.18%）**，仍未达标。此次只复核原件算术、原classify函数选定文件集、Git对象字节与计量脚本身份，**没有重跑cloc、测试、benchmark、HTTP/SQL/云或服务**。

正式口径不变：已提交backend/t44/、frontend/src/及frontend/index.html中.py/.ts/.vue/.css/.html的非空非注释物理源码行；测试/部署/DDL/配置原本另列，不是本轮排除。计量脚本与C逐字同，cloc工具原SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83；应用66文件集合与原件一致，本岗HEAD应用三根与C逐字同。逐文件Git blob/原cloc数在static-receipt.json。旧bc5的6307不能覆盖D008后的6310，也不重写旧记录。

## 已有分析直接复用，不刷实验或重启已拒路线

- 原source-budget-profile/n07-source-budget-one-page.md与result.md已说明没有可信1207删除方案；当前差额随D008变为1210。大文件seed370、migration321、Rows299、Runtime276含已要求功能，不能整块扣掉、迁出计量根或转成不计数配置。
- 旧validator C草案55→45、静态-10：本次只核其before源码SHA仍与C相同。旧19有限样本/构造占比3.7094%的运行属于当时bc5/Spec，**不移植为C1.2全部HTTP、$id/ref/format或线程等价证明**。原型未准入/未应用，实际节省0；不为10行直接引入该语义风险。
- 先前拒绝的AST/scan-dedup不复活，不把14字段毛片段当净省。既有Call.create/cas、common.model/page已集中不少职责，不能再次按原毛行数重复扣减。domain typed守卫、持久层证据/CAS、API请求/响应/历史数据校验守不同入口，不是可直接删除的同一责任。

## 一个可审的小抽象：通知分页复用现有page

这是既有profile中“通知分页职责重叠”的具体化，不是实施准入。涉及backend负责common.page与消息岗NotificationFacade.list，须两owner/root复核后另派；本轮不修改任何产品文件。

**接口：** `page(g, table, where, query, serialize, *, predicates=(), order_by=None) -> {items,page,page_size,total}`。只增加受信内部keyword，默认None完全保留原`(query.sort或id,id)`顺序；传入非空受信tuple时按其排序。不是新增HTTP参数，不允许客户端选择表/任意SQL，不去掉原Rows字段/排序白名单。原函数没有类型注解，本设计不删除其它类型/守卫；未来审核增加必要声明/校验导致不省时应放弃此小项。

**调用与输出：** NotificationFacade.list前半部项目/本人membership实时校验及S锁不动，保持原where(recipient_id+authorized projects)、read/handled谓词，调用page传同一g、query、notification序列化器、`order_by=("-id",)`；再附原unread_count和unhandled_count。原`notification()`对fallback的bool转换保留。接口/分页/输出字段逐字语义不变。

**重要边界：** 不开新UoW/不提交/不提前释锁，不缓存身份或改变撤权语义；授权/输入/错误优先级保持。仍是同样的rows、过滤total COUNT以及两个基于where的未读/未处理COUNT，**后两者不能错误继承read/handled筛选谓词**。rows→序列化→total→unread→unhandled的顺序保持，两个附加COUNT不可删。只去重复分页组装，不宣称减少SQL、连接数或P95；空集是否发SQL仍由既有Gateway处理。

受信改动示意（不应用，保持逐参数排版）：

```python
result = page(
    g,
    "notifications",
    where,
    query,
    notification,
    predicates=predicates,
    order_by=("-id",),
)
return {
    **result,
    # 原unread_count/unhandled_count两项原样保留
}
```

**预算：** 现有独立分页装配片段14个非空源码行可被上方相同逐参数风格的11行替代；common.page的签名/原order_by表达式各原位替换，import扩展仍一行，初估仅 **净-3行**。这是未应用文本的工程预估，不是新的cloc结果；不得通过压排版兑现。若实际格式化/必要边界使净不省，则不做。它并不能解决1210缺口，不建议为这3行优先支付跨模块回归成本。

**后续验证计划（本轮不执行）：** 同一受信g的调用/顺序与响应前后等价；显式项目/全部有效成员项目、空项目集合、分页边界、未读/处理四筛选组合、total与两全范围计数区别、通知降级bool、原降序稳定性/本人限定/撤权后的新请求拒绝；其它page调用者默认顺序不变。保留旧断言，真实HTTP/DB范围另准入，不以镜像实现的常量测试代替。

## 推荐与不确定性

实际净节省仍 **0**。仅作上界理解：假设未应用的旧-10未来全部证明落地，也只是6300/仍超1200；再假设上述-3成立才是6297/仍超1197，不计入现行结果。没有证据支持可读/等价删去1210行的计划。继续如实标N07未达标；更大架构/课程范围取舍需root与人另定，不能默认放宽3500–5100或为数值删功能/测试/审计/类型。

依据：[准确C原计量](../release-error-priority-implementation/source-count.json)、[既有预算](../runtime-plan-loc-budget.json)、[旧一页分析](../source-budget-profile/n07-source-budget-one-page.md)、[旧有限诊断](../source-budget-profile/result.md)、[根取舍材料](../../../docs/reviews/source-budget-decision-options.md)。不接触852/841任何未公开材料，不与tester交流；RequestID候选及其CI由部署岗另行负责，不混入本设计或云C身份。
