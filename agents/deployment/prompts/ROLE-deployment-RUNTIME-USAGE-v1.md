# ROLE-deployment-RUNTIME-USAGE-v1

本岗为实际派工建归档ID，不称用户迭代。

## 总协调实际派工原文

现在有槽，开始预告的中性runtime-usage新阶段。root当前7f2cced4063d445f96707f9274b666e03ad697c6，建议从此新codex/deployment-runtime-usage独立branch/worktree，不污染旧wrapper历史。先读root先行RFC specs/changes/runtime-usage-snapshot-rfc.md（db7df7），按JSON/CLI字段合同实现：control.py runtime-usage无任意参数、固定验证本次六服务唯一64hex ID/project/service标签→一次有界docker stats --no-stream --no-trunc固定只含ID/CPUPerc/MemUsage/MemPerc/NetIO/BlockIO/PIDs的格式输出，仅内存白名单投影/丢弃stderr不泄原异常。0仅六项完整，非0+单JSON稳定errors/null/时间包围，缺/重/外来ID/停止/超时严格诚实。run.py只新增context runtime_usage声明，不自动采样；旧metadata/controls输出/应用/frozen全不变。CLI内存扣缓存非RSS，PIDs含线程、格式累计IO非速率、CPU窗口非600s、样本非原子/非峰值/调用开销保留，都写文档。若合同必须变先设计显式说明并root报告，不静默改。测试已root预留tmp/deployment/865_runtime_usage.py，仅有意义的合成完整/异常/验证/无秘密/旧接口兼容目标，不新建散落test文件，不重复旧已通过suite。本机native唯一360正在跑，严禁HTTP/SQL/Docker服务/OS信号或读取任何独立资料；没有本机Docker就如实合成，后由独立tester实采。官方根已核stats文档链接在RFC，技术不确定只用Docker官方主源。约15分钟有界交付：代码/必要guard/Ruff/真实红绿/sourcehash/WORKLOG/module/handoff/actualPrompt/Issue7真实发问或交接+完整GETreadback，准确最终SHA推送。可以只skipci工具阶段，root静态接线审核后给tester准确环境绑定；不宣正式性能、生产准入或补过去unknown。

## 对应产物/边界

独立usage.py、CLI/context声明、原编号865合成guard、README/格式示例与本岗原件。RFC字段不变；失败批次全部统计null、稳定码，未验证身份null，验证成功ID可保留；这些是合同内实现解释。只新865/变更Ruff，不跑旧suite、HTTP/SQL/Docker/OS信号，不读独立材料。
