Agent-Role: backend（AI归档操作者；不是原托管CI执行者/学生人工验证）
Prompt-Ref: agents/backend/POOL-CANDIDATE-CI-ARCHIVE-dispatch.md

候选db87d30449356f3473b645a5c246dcc6c21d7cbe的product push40039282322与Docker PR40039333270均官方completed/success；只读取这两次开发CI，未触发新CI或本机业务HTTP/SQL/负载。五个官方ZIP均先核API sha256 digest再开包，按旧清单只选新18+33原件gzip并逐项原/gzip hash及实际roundtrip；原ZIP留ignored私密目录。没有复制旧结果或读独立日志/密文。

新JUnit520/0failure/error/skip，其中869离线QueuePool/合成DBAPI+Settings十例实际收集；930无testcase，pytest可能导入模块不等于执行其opt-in对照负载。marker162/93/19与520重叠，不相加。全部44Python文件集合精确等于候选Git，excluded0，行2638/2957=89.2120%、分支659/824=79.9757%分别列（原combined87.199%不是行覆盖）；FE89全部通过，20TS/Vue文件与Git精确一致，行93.33%/分支88.09%，不冒CSS/HTML覆盖。

Docker APIhead是db87，但实际checkout是400a5cac444be15565dc48fe4ee2a1869f31e9a3：官方checkout步骤真实git checkout PR39/merge、git log -1完整SHA已留原行/行号/哈希。result.source_sha本身取GITHUB_SHA，只作为旁证。实际Git对象父base70f4b7+db87；166个明确运行roots文件（完整backend/frontend/deployment/scripts/.github/compose、运行contracts/DDL及相关CI入口/测试）与候选逐字相同，不声称两个整提交相同。

Docker实际1parent/4workers，扫描created16/completed2，合成2项目40任务30依赖，19表行数/校验和恢复全相等（其中18业务表226列）；唯一预期nonzero为第二scanner flock拒绝exit1。未测容器活跃连接数，不能据源码默认推已观测90连接。

准确汇总records/validation/composite-db87-pool-ci.json，原件records/ci/40039282322与40039333270。首gh日志获取因ANSI保护退出1、修正仅官方读取flag，以及本地缺merge对象后显式fetch均保留，不是CI失败/重跑。生产integration仍bc5、6307超1207保持；此归档不是专审/生产准入、正式性能或独立验收通过，后续由root与专审另决。
