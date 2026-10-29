# 通知 Call 接口与 CAS 复用：实际交付

实际操作者 messaging AI；提示词 ROLE-messaging-COMPONENT-CALL-20261028-v1。设计82b6e576先于本岗代码。基线5d，经后端产品2d947d23提供固定组件分派与Call.cas开关，本岗产品为 `6977e5b7331e4c6cf64b719b6f161a082558ef25`。这是开发候选，不是本人研究正文或独立验收。

## 实现与接口

唯一消息生产变更为NotificationFacade：list/mark_read/handle输入(g,c)，资格/项目/收件人/版本/值构造顺序保留。`_update`先显式check_version再惰性values，再调用原cas(record_diff=False)。False保持原before/after列表，Runtime.audit仍执行；handle不自动已读。外部REST/OpenAPI/DDL、SQL锁/UoW、outbox、broker、consumer均未修改；旧平铺Python接口是明确内部迁移，没有产品兼容壳。

旧979/806全部测试函数定义和36个assert AST逐序相等，freeze与compare JSON可复算。只把模块中的调用者绑定到tmp/780里的test-only适配器，将旧夹具参数构造真实Call；create_app仍装真实生产NotificationFacade。新增7边界直接调用新生产接口，不经过该适配器，防止仅靠旧调用包装掩盖迁移问题。

## 真实执行

解释器为现有backend worktree的Python3.12虚拟环境，PYTHONPATH=backend；本岗没有安装依赖或读取凭据。所有命令在本岗隔离worktree执行，均使用`-c backend/pyproject.toml`。

| 检查 | 实际结果 | 原件 |
| --- | --- | --- |
| 新780边界在未迁移通知源码上 | 7失败，都是旧平铺签名TypeError；这是迁移前基线，不伪称7个旧业务缺陷 | before-direct.log/xml |
| 新780边界在候选上 | 7通过 | after-direct.log/xml |
| 原消息+782+780，排除integration | 60通过，23未执行 | joint-module.log/xml |
| 原contracts/API+782+780，排除integration | 164通过，40未执行，61.36秒 | joint-api.log/xml |
| 本岗scoped Ruff | 首轮I001导入顺序失败；仅排序后exit0 | lint-first/import-fix/final.log |
| 固定source_count.py/cloc2.10 | 5898/within_range=false/exit1 | source-count-after.json |

两联合套件交集21、成功唯一并集203，不能写成224个不同成功用例；新7和782的14均重复在两套内。原backend曾报告的默认通知空列表500在本轮原API断言中实际转绿，未改该外岗测试。pytest有现有httpx/Starlette弃用警告，未为本重构改依赖。

上述开发测试先对工作树候选执行，随后提交6977，产品/测试在提交期间未更改；不声称它们是预先checkout6977的托管CI。准确源的完整CI应由总协调另行执行。XML及日志原字节保留，verification.json记录SHA和逐项结果，失败不改成成功。

## 规模与未闭合项

固定应用计量65文件：5d5935→后端5916→联合5898，消息facade85→67，**本岗净18，合包净37**。后端收益19不重复归本岗；严格上限5100仍超798，计数器及原分母未改。没有压行、删除功能或迁生产代码到排除路径；tmp/780只有测试和旧夹具调用适配。

原生MySQL并发、RabbitMQ、完整覆盖率/CI、云、独立验收和400活跃并发600秒正式性能均未执行。新7测试位于tmp/780，完整coverage job目前不会自动收集，已通知总协调显式接入原CI列表；没有越岗改CI。当前云候选仍5d，6977待审核及整合。
