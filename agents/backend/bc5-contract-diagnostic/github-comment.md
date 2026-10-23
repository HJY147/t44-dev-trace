Agent-Role: backend
Prompt-Ref: agents/backend/BC5-CONTRACT-DIAGNOSTICS-dispatch.md

bc5固定应用的有界开发诊断已结束，生产/SQL/锁/资源/14冻结均未改。本轮由后端AI执行，不是学生手改或独立验收。

设计08f8050d先行、工具231445d后执行。原批exit1：baseline并发1/8/32分别975/1562/1229请求、全部有效，P95=3.681/24.383/87.779ms；timings新包装首参与FastAPI真实function=转发相撞，造成非JSON500/连接异常，0请求进入runtime。原失败保留，不归产品500/503。根另准入只续未完成范围，先44b9e8c设计/工具修正，真实FastAPI/AnyIO离线一次透明转发证明后，显式continuation exit0：3416 timings+3 profile全部有效，无重复bootstrap/sanity/baseline。

所有3419观测request_id精确关联，恰1acquire/1实时auth/1派发入口，三类候选实际SELECT4/5/5、0SQL错误。timings1/8/32 P95=4.199/25.010/89.705ms；并发32平均runtime wall28.630ms、同线程CPU1.766ms、cursor wall9.239ms、acquire14.525ms、dispatch-to-entry6.123ms。inclusive重叠不能相加，也不把acquire叫纯poolwait/dispatch叫纯排队。DBAPI新连1/69/211次是后续连接生命周期观测线索，不能直接据此调池；schema构造约0.04ms/请求，没有优先应用C的证据。

范围仅本岗t44_profile/18083/单worker；两次前后端口空、本库其他连接0、自有进程正常退，仅原bootstrap新增自有project44/task6004等，未清库或重seed。三类契约候选不是三正式入口，未复现503/未跑transition或escalation、未采MySQL server锁等待，不能解释已发表托管400×600三组失败。后续需要根另准入写路径结构化503与同次阶段/安全DB错误分类观测，不能用本机短样本填正式缺项。源码固定6307仍超1207，C/B仍未应用。

结果和完整方法：agents/backend/bc5-contract-diagnostic/result.md、design.md、summary.json、continuation-summary.json。原49份选定安全原件gzip及双SHA分两份manifest，原失败与续跑分别绑定；fixture/token排除。本阶段封档后释放，无新全CI/负载或生产优化准入请求。
