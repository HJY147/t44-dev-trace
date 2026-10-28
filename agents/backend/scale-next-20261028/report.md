# 真实重复规则重构：净减4行，仍超794

后端AI从精确f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f新建`codex/backend-scale-next-20261028`；设计先提交50b52755，产品候选为5cd0ad43d93bb9066e67bda04337815e6f6fa1b1。20Z/P64/原source/云版本均未修改，本岗没有云、SUT、CI或独立私件访问。

固定source_count.py、固定cloc2.10（SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83）对已提交源实测5898→5894，**净减4，仍高于5100共794**。两次`--require-range`真实退出1，未达标。初始10–15行设计预算算少了完整helper定义/返回成本，实际只Reviews3、Tasks1；本报告不沿用该预测，也不以工具/测试行数充当应用收益。

`Reviews._assessment_versions`统一原两处“按rollback_plan_version倒序取一个”的查询策略；保留原task归属、权限、状态、责任人校验时点、原列表返回及创建空列表版本1/审核原`[0]`行为。`Tasks._editable_task`统一三个编辑操作的manager→task→prestart顺序，各操作仍传原错误码，后续owner、乐观版本、人力容量、重复/环依赖、CAS和审计都留原位置。没有新增SQL或事务，也未更改HTTP/OpenAPI/DDL/消息或其他岗内部契约。

43个场景将f7原服务模块从确切Git对象载入，与候选使用相同真实Call和可追踪内存网关，比较返回、异常类/消息/属性、SQL网关调用顺序/参数、数据行及audit before/after。覆盖创建/审核评估、转派、增删依赖的成功、blocked-from-pending、权限与缺资源同时失败、版本/容量、旧评估/基线等。额外1项验证故意“先查task再manager”的本地错误mutant确实与原双错误场景不同；这证明测试能辨别优先级，**不是原产品红例或已修缺陷**。重构前后各44通过，不能合计88个独立场景。

原986_http.py限定相关7个测试名称及其参数化场景：17 passed、106 deselected，涵盖评估取代批准、完整交付/回滚/返工、依赖环/编辑锁/删除、转派人力与既有错误优先级。原文件逐字未改，所有原断言保留。SQLite/TestClient不是MySQL锁/正式性能/独立验收。此次从根目录调用未指定backend pytest配置，出现3条未注册marker warning；另1条为既有Starlette/httpx弃用warning，均未改测试/依赖来消除。最终限定Ruff/diff检查通过。

过程真实问题：新worktree尚在checkout时，本岗曾提前执行读取，得到文件不存在；随后改从已知f7 Git对象只读，待checkout完成再写设计/产品。新自测首次Ruff报import顺序和宽异常捕获；修顺序，并为“逐类比较全部原异常”的测试目的写明局部noqa，不给产品加宽异常吞掉问题。没有产品红转绿，不伪造过程。

## 重现与范围

```sh
PYTHONPATH=backend <APPROVED_PYTHON> -m pytest tmp/779_backend_scale_next_20261028/779_service_differential.py -q
PYTHONPATH=backend <APPROVED_PYTHON> -m pytest tmp/backend/contracts/986_http.py -q -k 'new_assessment_supersedes or complete_delivery_rollback_rework or dependencies_cycle_guard or dependency_remove_and_last_manager or capacity_v11_assignment or capacity_v11_keeps_original_guard_precedence or reject_review_new_cycle'
python3 scripts/metrics/source_count.py --cloc '<VERIFIED_CLOC_2_10>' --output '<NEW_OUTPUT>' --require-range
```

before/after-source-count.json、两次differential JUnit、existing-targeted-http.xml和verification.PUBLIC.json在`tmp/779_backend_scale_next_20261028`。计数绑定5cd0ad43，后续本岗报告提交仅文档/证据，不改变这两个产品字节。全CI和云源替换须root另行集成，不能把本自测记为review已通过。

更大的安全收益尚无证据：后端服务已由Call/CAS/page/model共用，剩余校验多是不同错误优先级/锁时点或业务规则。将typed-row校验放同一循环会让task身份错误抢在review计数错误之前；wire与normalized的tuple/datetime/Decimal语义也不同，不能仅凭外形相同合并。既有跨岗架构报告A已兑现37行不能重算，B/C/E等尚需owner逐项确认且总量远小于794。建议root把本4行视作可单独取舍的维护性候选，继续只接纳有完整接口/行为证据的跨岗方案；本轮没有798行闭合设计，不制造大抽象或压行凑数。
