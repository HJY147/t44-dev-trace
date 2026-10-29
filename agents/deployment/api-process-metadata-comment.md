Agent-Role: deployment
Prompt-Ref: ROLE-deployment-API-PROCESS-METADATA-v1

已push中性API进程识别窄修 `c0a5e89b2442da2a9149e1d37c2a424d52aff7c0`，分支codex/deployment-api-process-metadata，基点 `5148733398868002eb4eafad6a9ea207defe0412`。

先记录设计与原源SHA，再仅在既有953构造fake /proc：init/tini wrapper的argv尾部包含相同uvicorn命令，另有Python -m uvicorn模块形态进程和4个spawn条目。原API_SCRIPT两例真实红：supervisor_count=2、configured_workers=[4,4]。这只确认合成输入误计，不是stage05实际故障原因判断；未读取旧raw或任何独立私密资料。

窄修只匹配Python executable basename及紧邻 `-m uvicorn t44.api:app` argv前缀，不再把wrapper尾部参数作为supervisor身份。`api_projection`仍严格要求恰好1个；未增加数量容忍、默认worker值或资源。相同两反例、两个实际Python模块形态条目仍被拒绝、原API projection守卫，共4项合成green；74无关项未运行。Ruff通过；AST证明除API_SCRIPT外全部相同。首次green的转义warning原件保留，改正正则字面形式后同4项无warning通过。

设计与红/绿stdout、stderr、JUnit、源SHA/AST证据在agents/deployment/api-process-metadata-validation及本岗design文件。原红JUnit尾空白导致第一次diff-check失败，原字节gzip+SHA保留，阅读稿仅规范尾空白；最终diff-check通过。不改b3ee/H11历史incomplete或原正式封存失败，不倒填元数据。

请总协调仅将此标为采集器合成边界修复；真实stage05原因仍unknown，没有新的真实runner完整快照。未运行Docker、真实/proc/业务进程采集、旧故障复测或压力；未改产品/native/资源/性能阈值，也未与独立岗通信。
