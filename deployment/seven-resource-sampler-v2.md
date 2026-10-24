# 七服务采样v2窗口变更（仅能力交付）

v2为独立新文件seven-resource-sampler-v2.py；原fe5dad…37af版本及08:44Z截止不改，不停止当前云运行。root审核新hash后另行执行 `python3 /run/t44-delivery/seven-resource-sampler-v2.py`，无参数。计划正式测试前启动以覆盖新窗口，不宣称实际启动或完成。

唯一代码差异：绝对截止2026-10-24T10:10:00Z（北京18:10），最长5400秒（90分钟）；对应datetime时/分、stop cap、context cap/UTC string共5个AST Constant，其余AST严格一致，反向4处文本替换恢复原bytes。原固定七服务/只读映射/字段/私有输出/10秒目标/实际overhead及全部限制保持；不读取独立资料，不作性能结论。

用户明确预算100 CNY并完成SMS；两机自动释放北京18:30据root实际UI核实，正式独立测试计划18:10硬停，理由是覆盖新的正式窗口并留收尾时间。**100元是用户授权预算上限，不是实际已消费100元**；本岗不操作资源或支付，不改其他旧工具截止。新时限不回写旧日志/旧采样器/已经执行的任务，不kill/重启旧实例；双采样若实际重叠须如实记录额外开销，不称零影响。

本地仅源码差量AST/字节校准、Ruff/compile/diff-check；不重复原8guard、不建新test文件（844未使用），不执行任何collector或云/Docker/proc/服务。实际v2回执/样本仍待root另取，当前能力通过不等于正式测试完成。
