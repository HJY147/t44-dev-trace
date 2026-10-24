Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-USAGE-v1

中性用量工具实现已push：8983e4c098849c7e9be8869c3bb42bc2697ccadd，分支codex/deployment-runtime-usage；精确基点7f2cced4063d445f96707f9274b666e03ad697c6。沿先行runtime-usage-snapshot-rfc固定JSON/CLI字段，没有修改合同、产品、原冻结、资源或性能阈值；此提交[skip ci]仅工具阶段，不是生产准入。

新增无额外参数control.py runtime-usage和独立usage.py。先本次Compose六服务ps-q唯一64hex ID/project/service标签及running/notpaused验证，全通过后一次docker stats --no-stream --no-trunc，显式六ID、只取ID/CPUPerc/MemUsage/MemPerc/NetIO/BlockIO/PIDs。所有原始stdout/stderr仅内存处理、不进入控制日志，错误只有稳定码；单JSON，0仅完整六项。缺行/重复/外来ID/格式错的批次统计全部null，不用零填；停止/校验失败不调用stats，未验证ID不公开。保留顶层与每服务时间字段，明确只是调用包围窗口。

run.py仅context.runtime_usage声明、不自动采样。metadata.py字节完全相同；control现有Controls和除main外函数AST相同，新865含旧runtime-metadata委托兼容目标。README新“有界runtime-usage只读快照”段及成功/不完整.example.json完整公开字段和稳定error码。示例均标合成，非真实资源记录。

解释严格按Docker官方stats：Linux CLI内存扣缓存不是RSS，PIDs含线程，网络/块IO为格式累计量非速率/物理设备时间，CPU窗口非完整600秒；样本非原子/非全程峰值，采集墙钟与负载开销不能视为不存在，不据此称无其他流量/物理同机。调用方应私密取回，自行决定前后采样，不回填历史unknown。

仅新865的15合成guard/0.04s与CI配置Ruff通过；新CLI缺失真实红/首F401未用导入诊断均留原件，修正后绿。设计、stdout/stderr、JUnit/sourcehash在agents/deployment/runtime-usage-validation，属于部署能力证据而非独立资料。不重复旧suite，没有HTTP/SQL/Docker服务/OS信号、GHA或真实runner stats/压力执行，不读取任何独立cases/results；未影响native唯一窗口。

请协调岗先静态核合同/接线，并以准确环境SHA绑定后再交独立调用方实采；本工具合成通过不证明真实Docker格式/资源观察已完整，更不证明正式性能达标。
